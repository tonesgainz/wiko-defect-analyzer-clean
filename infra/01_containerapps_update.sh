#!/usr/bin/env bash
set -euo pipefail

# Expected env vars:
# RG=rg-wiko-ai
# LOCATION=canadacentral
# CONTAINER_APP=wiko-defect-analyzer
# STORAGE_ACCOUNT=wikosa<unique>
# SB_NAMESPACE=wiko-sb
# SERVICE_BUS_QUEUE=defect-jobs
# APP_INSIGHTS=appi-wiko-ai
# KEY_VAULT=kv-wiko-ai

: "${RG:?Set RG}"
: "${CONTAINER_APP:?Set CONTAINER_APP}"
: "${STORAGE_ACCOUNT:?Set STORAGE_ACCOUNT}"
: "${SB_NAMESPACE:?Set SB_NAMESPACE}"
: "${APP_INSIGHTS:?Set APP_INSIGHTS}"
: "${KEY_VAULT:?Set KEY_VAULT}"
SERVICE_BUS_QUEUE="${SERVICE_BUS_QUEUE:-defect-jobs}"

echo "Updating Container App '${CONTAINER_APP}' in RG='${RG}'"

STORAGE_SCOPE="$(az storage account show -n "${STORAGE_ACCOUNT}" -g "${RG}" --query id -o tsv)"
SB_SCOPE="$(az servicebus namespace show -n "${SB_NAMESPACE}" -g "${RG}" --query id -o tsv)"
KV_SCOPE="$(az keyvault show -n "${KEY_VAULT}" -g "${RG}" --query id -o tsv)"
APPINSIGHTS_CONN="$(az monitor app-insights component show --app "${APP_INSIGHTS}" -g "${RG}" --query connectionString -o tsv)"

STORAGE_ACCOUNT_URL="https://${STORAGE_ACCOUNT}.blob.core.windows.net"
SERVICE_BUS_NAMESPACE_FQDN="${SB_NAMESPACE}.servicebus.windows.net"

echo "Ensuring managed identity is assigned..."
az containerapp identity assign --name "${CONTAINER_APP}" --resource-group "${RG}" --output table
PRINCIPAL_ID="$(az containerapp show --name "${CONTAINER_APP}" --resource-group "${RG}" --query identity.principalId -o tsv)"

echo "Setting environment variables..."
az containerapp update \
  --name "${CONTAINER_APP}" \
  --resource-group "${RG}" \
  --set-env-vars \
    AZURE_STORAGE_ACCOUNT_URL="${STORAGE_ACCOUNT_URL}" \
    AZURE_STORAGE_CONTAINER_RAW=raw-images \
    AZURE_STORAGE_CONTAINER_PROCESSED=processed-images \
    SERVICE_BUS_NAMESPACE_FQDN="${SERVICE_BUS_NAMESPACE_FQDN}" \
    SERVICE_BUS_QUEUE="${SERVICE_BUS_QUEUE}" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="${APPINSIGHTS_CONN}" \
  --output table

echo "Assigning RBAC to managed identity..."
az role assignment create --assignee "${PRINCIPAL_ID}" --role "Storage Blob Data Contributor" --scope "${STORAGE_SCOPE}" --output table
az role assignment create --assignee "${PRINCIPAL_ID}" --role "Azure Service Bus Data Sender" --scope "${SB_SCOPE}" --output table
az role assignment create --assignee "${PRINCIPAL_ID}" --role "Azure Service Bus Data Receiver" --scope "${SB_SCOPE}" --output table

if [[ "${ASSIGN_KEYVAULT_ROLE:-true}" == "true" ]]; then
  az role assignment create --assignee "${PRINCIPAL_ID}" --role "Key Vault Secrets User" --scope "${KV_SCOPE}" --output table
fi

echo "Done. Updated env vars and RBAC for '${CONTAINER_APP}'."
