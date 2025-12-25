# Azure Infra Scripts (async ingest)

Run these locally; do not run from Codex. Order:
1. `infra/00_bootstrap.sh` – create or validate the core resources (RG, Storage, Service Bus, Log Analytics, App Insights, Key Vault).
2. `infra/01_containerapps_update.sh` – assign Container App managed identity, set env vars, and grant RBAC to Storage/Service Bus/Key Vault.
3. `infra/deploy_worker_containerapp_job.sh` – build/push worker image to ACR and deploy a Container Apps Job that scales on Service Bus messages.

Recommended env exports before running (edit to your naming/region; storage and vault names must be globally unique):
```bash
export RG=rg-wiko-ai
export LOCATION=canadacentral
export STORAGE_ACCOUNT=wikosa<unique>
export SB_NAMESPACE=wiko-sb
export LOG_ANALYTICS=law-wiko-ai
export APP_INSIGHTS=appi-wiko-ai
export KEY_VAULT=kv-wiko-ai
export CONTAINER_APP=wiko-defect-analyzer
export CONTAINER_APP_ENV=wiko-ca-env   # if needed by your setup
export SERVICE_BUS_QUEUE=defect-jobs
```

After provisioning, set these app env vars (script 01 does this):
- `AZURE_STORAGE_ACCOUNT_URL=https://$STORAGE_ACCOUNT.blob.core.windows.net`
- `AZURE_STORAGE_CONTAINER_RAW=raw-images`
- `SERVICE_BUS_NAMESPACE_FQDN=$SB_NAMESPACE.servicebus.windows.net`
- `SERVICE_BUS_QUEUE=$SERVICE_BUS_QUEUE`
- `APPLICATIONINSIGHTS_CONNECTION_STRING` from App Insights.
