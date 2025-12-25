#!/usr/bin/env bash
set -euo pipefail

# Expected env vars (edit to your naming/region; storage/vault must be globally unique):
# RG=rg-wiko-ai
# LOCATION=canadacentral
# STORAGE_ACCOUNT=wikosa<unique>
# SB_NAMESPACE=wiko-sb
# LOG_ANALYTICS=law-wiko-ai
# APP_INSIGHTS=appi-wiko-ai
# KEY_VAULT=kv-wiko-ai
# SERVICE_BUS_QUEUE=defect-jobs

: "${RG:?Set RG}"
: "${LOCATION:?Set LOCATION}"
: "${STORAGE_ACCOUNT:?Set STORAGE_ACCOUNT (globally unique, lowercase letters/numbers)}"
: "${SB_NAMESPACE:?Set SB_NAMESPACE}"
: "${LOG_ANALYTICS:?Set LOG_ANALYTICS}"
: "${APP_INSIGHTS:?Set APP_INSIGHTS}"
: "${KEY_VAULT:?Set KEY_VAULT}"
SERVICE_BUS_QUEUE="${SERVICE_BUS_QUEUE:-defect-jobs}"

echo "Using RG=${RG} LOCATION=${LOCATION}"

echo "Ensuring resource group..."
az group create --name "${RG}" --location "${LOCATION}" --output table

echo "Ensuring storage account..."
az storage account show -n "${STORAGE_ACCOUNT}" -g "${RG}" >/dev/null 2>&1 || \
  az storage account create \
    --name "${STORAGE_ACCOUNT}" \
    --resource-group "${RG}" \
    --location "${LOCATION}" \
    --sku Standard_LRS \
    --kind StorageV2 \
    --output table

echo "Ensuring blob containers (raw-images, processed-images)..."
az storage container create --name raw-images --account-name "${STORAGE_ACCOUNT}" --auth-mode login --public-access off --output table
az storage container create --name processed-images --account-name "${STORAGE_ACCOUNT}" --auth-mode login --public-access off --output table

echo "Ensuring Service Bus namespace..."
az servicebus namespace show --name "${SB_NAMESPACE}" --resource-group "${RG}" >/dev/null 2>&1 || \
  az servicebus namespace create --name "${SB_NAMESPACE}" --resource-group "${RG}" --location "${LOCATION}" --sku Standard --output table

echo "Ensuring Service Bus queue (${SERVICE_BUS_QUEUE})..."
az servicebus queue create \
  --name "${SERVICE_BUS_QUEUE}" \
  --namespace-name "${SB_NAMESPACE}" \
  --resource-group "${RG}" \
  --max-delivery-count 10 \
  --output table

echo "Ensuring Log Analytics workspace..."
az monitor log-analytics workspace show --workspace-name "${LOG_ANALYTICS}" --resource-group "${RG}" >/dev/null 2>&1 || \
  az monitor log-analytics workspace create --workspace-name "${LOG_ANALYTICS}" --resource-group "${RG}" --location "${LOCATION}" --output table

echo "Ensuring Application Insights (linked to workspace)..."
az monitor app-insights component show --app "${APP_INSIGHTS}" --resource-group "${RG}" >/dev/null 2>&1 || \
  az monitor app-insights component create \
    --app "${APP_INSIGHTS}" \
    --location "${LOCATION}" \
    --resource-group "${RG}" \
    --workspace "${LOG_ANALYTICS}" \
    --output table

echo "Ensuring Key Vault..."
az keyvault show --name "${KEY_VAULT}" --resource-group "${RG}" >/dev/null 2>&1 || \
  az keyvault create \
    --name "${KEY_VAULT}" \
    --resource-group "${RG}" \
    --location "${LOCATION}" \
    --enable-rbac-authorization true \
    --output table

echo "==== Resource summary ===="
az group show -n "${RG}" --query id -o tsv
az storage account show -n "${STORAGE_ACCOUNT}" -g "${RG}" --query id -o tsv
az servicebus namespace show -n "${SB_NAMESPACE}" -g "${RG}" --query id -o tsv
az servicebus queue show -n "${SERVICE_BUS_QUEUE}" --namespace-name "${SB_NAMESPACE}" -g "${RG}" --query id -o tsv
az monitor log-analytics workspace show --workspace-name "${LOG_ANALYTICS}" -g "${RG}" --query id -o tsv
az monitor app-insights component show --app "${APP_INSIGHTS}" -g "${RG}" --query id -o tsv
az keyvault show --name "${KEY_VAULT}" -g "${RG}" --query id -o tsv

echo "Done. No secrets were printed."
