"""
====================================================================
LAB 01/02 · Deploy model OpenAI: Standard / GlobalStandard / PTU
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI (management plane / ARM)
Biến .env    : AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AOAI_ACCOUNT_NAME
SDK tiền nhiệm: thao tác tay trên portal / gọi REST thuần.
Chạy         : uv run 01_foundry_setup_and_deployments/02_deploy_openai_model_standard_and_ptu.py
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── xác thực keyless ────────────────────────────────────────────
from azure.identity import DefaultAzureCredential

# ── SDK quản lý Cognitive Services / Azure OpenAI (ARM) ─────────
# azure-mgmt-cognitiveservices: tạo/liệt kê deployment model (management plane).
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import (
    Deployment, DeploymentProperties, DeploymentModel, Sku,
)


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def main() -> None:
    cfg = require_env("AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP", "AOAI_ACCOUNT_NAME")
    rg = cfg["AZURE_RESOURCE_GROUP"]
    account = cfg["AOAI_ACCOUNT_NAME"]

    credential = DefaultAzureCredential()
    client = CognitiveServicesManagementClient(credential, cfg["AZURE_SUBSCRIPTION_ID"])

    # 1) Tạo/cập nhật deployment.
    #    sku.name quyết định KIỂU triển khai:
    #      - "Standard"          : token-based, giới hạn theo region
    #      - "GlobalStandard"    : token-based, dung lượng toàn cầu
    #      - "ProvisionedManaged": PTU (mua throughput cố định, trả theo giờ)
    #    capacity: với Standard = nghìn-token/phút; với PTU = số PTU.
    deployment_name = "gpt-4o"
    print(f"Đang tạo deployment '{deployment_name}' (GlobalStandard) ...")
    poller = client.deployments.begin_create_or_update(
        rg, account, deployment_name,
        Deployment(
            sku=Sku(name="GlobalStandard", capacity=10),
            properties=DeploymentProperties(
                model=DeploymentModel(format="OpenAI", name="gpt-4o", version="2024-11-20"),
            ),
        ),
    )
    poller.result()
    print("  -> Xong.")

    # 2) Liệt kê deployment + đọc sku/capacity
    print("\nCác deployment hiện có:")
    for d in client.deployments.list(rg, account):
        sku = d.sku
        print(f"  - {d.name}: sku={sku.name}, capacity={sku.capacity}, "
              f"model={d.properties.model.name}:{d.properties.model.version}")

    # 3) (tuỳ chọn) xoá deployment test để khỏi tốn tiền:
    #    client.deployments.begin_delete(rg, account, deployment_name).result()
    print("\nMẹo: xoá deployment test bằng client.deployments.begin_delete(...) để tránh phát sinh phí.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
