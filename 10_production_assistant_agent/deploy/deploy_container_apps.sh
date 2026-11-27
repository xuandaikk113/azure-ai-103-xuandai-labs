#!/usr/bin/env bash
# Deploy trợ lý lên Azure Container Apps (minh hoạ best practice: keyless + managed identity).
# Yêu cầu: az CLI đã login (az login) + đã có resource group + Container Apps environment.
# Chạy: bash deploy/deploy_container_apps.sh
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-ai103-rg}"
LOCATION="${LOCATION:-eastus}"
ENVIRONMENT="${ENVIRONMENT:-ai103-aca-env}"
APP_NAME="${APP_NAME:-assistant-agent}"
ACR_NAME="${ACR_NAME:-ai103acr}"              # Azure Container Registry (phải unique toàn cầu)
IMAGE="${ACR_NAME}.azurecr.io/${APP_NAME}:latest"

# 1) Build & push image (ACR tự build từ Dockerfile, khỏi cần Docker local).
az acr build --registry "$ACR_NAME" --image "$APP_NAME:latest" .

# 2) Tạo Container App với system-assigned managed identity (KHÔNG dùng secret/API key).
az containerapp create \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENVIRONMENT" \
  --image "$IMAGE" \
  --target-port 8080 \
  --ingress external \
  --system-assigned \
  --env-vars ASSISTANT_LLM_PROVIDER=foundry \
             FOUNDRY_PROJECT_ENDPOINT="$FOUNDRY_PROJECT_ENDPOINT" \
             FOUNDRY_MODEL="${FOUNDRY_MODEL:-gpt-4o}"

# 3) Gán RBAC cho managed identity của app để gọi Foundry keyless (role Foundry User).
#    PRINCIPAL_ID lấy từ: az containerapp show --query identity.principalId -o tsv
echo "Tiếp theo: gán role 'Foundry User' cho principalId của app trên Foundry project (xem lab 00/04)."
echo "Deploy xong. Lấy URL: az containerapp show -n $APP_NAME -g $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv"
