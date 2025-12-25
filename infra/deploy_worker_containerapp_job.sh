#!/usr/bin/env bash
set -euo pipefail

# Build and deploy worker as Azure Container Apps Job (event-driven via Service Bus/KEDA).
# Expected env vars (edit to your naming/region; ACR names must be globally unique):
# RG=rg-wiko-ai
# LOCATION=canadacentral
# CONTAINER_APP_ENV=wiko-ca-env
# JOB_NAME=wiko-defect-worker
# ACR_NAME=wikoregistry
# IMAGE_NAME=wiko-defect-worker
# IMAGE_TAG=latest
# STORAGE_ACCOUNT=wikosa<unique>
# SB_NAMESPACE=wiko-sb
# SERVICE_BUS_QUEUE=defect-jobs
# APP_INSIGHTS=appi-wiko-ai

: "${RG:?Set RG}"
: "${LOCATION:?Set LOCATION}"
: "${CONTAINER_APP_ENV:?Set CONTAINER_APP_ENV}"
: "${JOB_NAME:?Set JOB_NAME}"
: "${ACR_NAME:?Set ACR_NAME}"
: "${IMAGE_NAME:?Set IMAGE_NAME}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
: "${STORAGE_ACCOUNT:?Set STORAGE_ACCOUNT}"
: "${SB_NAMESPACE:?Set SB_NAMESPACE}"
SERVICE_BUS_QUEUE="${SERVICE_BUS_QUEUE:-defect-jobs}"

ACR_LOGIN_SERVER=$(az acr show -n "${ACR_NAME}" --query loginServer -o tsv 2>/dev/null || true)
if [[ -z "${ACR_LOGIN_SERVER}" ]]; then
  echo "Creating ACR ${ACR_NAME}..."
  az acr create --name "${ACR_NAME}" --resource-group "${RG}" --location "${LOCATION}" --sku Basic --output table
  ACR_LOGIN_SERVER=$(az acr show -n "${ACR_NAME}" --query loginServer -o tsv)
fi

echo "Building worker image..."
docker build -f worker/Dockerfile -t "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}" .
echo "Pushing worker image..."
az acr login --name "${ACR_NAME}"
docker push "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"

STORAGE_ACCOUNT_URL="https://${STORAGE_ACCOUNT}.blob.core.windows.net"
SERVICE_BUS_NAMESPACE_FQDN="${SB_NAMESPACE}.servicebus.windows.net"
APPINSIGHTS_CONN="$(az monitor app-insights component show --app "${APP_INSIGHTS}" -g "${RG}" --query connectionString -o tsv)"

echo "Creating/updating Container Apps Job..."
az containerapp job create \
  --name "${JOB_NAME}" \
  --resource-group "${RG}" \
  --environment "${CONTAINER_APP_ENV}" \
  --trigger-type Event \
  --replica-timeout 600 \
  --replica-retry-limit 3 \
  --replica-completion-count 1 \
  --min-executions 0 \
  --max-executions 5 \
  --image "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}" \
  --registry-server "${ACR_LOGIN_SERVER}" \
  --registry-identity system \
  --cpu 1 --memory 2Gi \
  --set-env-vars \
    AZURE_STORAGE_ACCOUNT_URL="${STORAGE_ACCOUNT_URL}" \
    AZURE_STORAGE_CONTAINER_RAW=raw-images \
    AZURE_STORAGE_CONTAINER_PROCESSED=processed-images \
    SERVICE_BUS_NAMESPACE_FQDN="${SERVICE_BUS_NAMESPACE_FQDN}" \
    SERVICE_BUS_QUEUE="${SERVICE_BUS_QUEUE}" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="${APPINSIGHTS_CONN}" \
  --scale-rule-name sb \
  --scale-rule-type azure-servicebus \
  --scale-rule-metadata queueName="${SERVICE_BUS_QUEUE}" namespace="${SERVICE_BUS_NAMESPACE_FQDN}" messageCount=5 \
  --scale-rule-auth managedIdentity=system \
  --output table

echo "Ensuring managed identity is assigned to job..."
az containerapp job identity assign --name "${JOB_NAME}" --resource-group "${RG}" --system-assigned --output table
PRINCIPAL_ID=$(az containerapp job show --name "${JOB_NAME}" --resource-group "${RG}" --query identity.principalId -o tsv)

STORAGE_SCOPE=$(az storage account show -n "${STORAGE_ACCOUNT}" -g "${RG}" --query id -o tsv)
SB_SCOPE=$(az servicebus namespace show -n "${SB_NAMESPACE}" -g "${RG}" --query id -o tsv)

echo "Assigning RBAC to job managed identity..."
az role assignment create --assignee "${PRINCIPAL_ID}" --role "Storage Blob Data Reader" --scope "${STORAGE_SCOPE}" --output table
az role assignment create --assignee "${PRINCIPAL_ID}" --role "Azure Service Bus Data Receiver" --scope "${SB_SCOPE}" --output table
az role assignment create --assignee "${PRINCIPAL_ID}" --role "Azure Service Bus Data Sender" --scope "${SB_SCOPE}" --output table

echo "Done. Job '${JOB_NAME}' configured (not executed)."
