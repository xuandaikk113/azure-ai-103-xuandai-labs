"""
====================================================================
LAB 00/01 · Provision Storage Blob — tạo storage account + container bằng code
--------------------------------------------------------------------
Dịch vụ      : Azure Storage (ARM / management plane)
Biến .env    : AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, STORAGE_ACCOUNT_NAME, AZURE_LOCATION
SDK tiền nhiệm: không (azure-mgmt-storage là SDK quản lý ARM hiện hành)
Chạy         : uv run 00_azure_foundations/01_provision_storage_blob.py
Blob dùng cho: RAG ingest (06/03), dịch document (07/05), dữ liệu fine-tune (01/06).
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os                       # đọc biến môi trường
import sys                      # thoát khi thiếu cấu hình

# Windows: console cp1252 không in được tiếng Việt -> ép UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv  # python-dotenv: nạp .env vào os.environ (tiện cho dev local)

# ── xác thực keyless ────────────────────────────────────────────
# azure-identity: lấy token Entra ID; cần role "Owner"/"Contributor" trên RG để tạo tài nguyên.
from azure.identity import DefaultAzureCredential

# ── SDK quản lý Storage (ARM) ───────────────────────────────────
# azure-mgmt-storage: tạo/sửa/xoá storage account & container (management plane).
# (Khác azure-storage-blob là SDK data plane dùng để ĐỌC/GHI blob.)
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountCreateParameters, Sku, BlobContainer


def require_env(*names: str) -> dict:
    """Nạp .env và đọc các biến bắt buộc; thiếu thì báo rõ rồi thoát."""
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def main() -> None:
    # 1) Đọc cấu hình
    cfg = require_env(
        "AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP",
        "STORAGE_ACCOUNT_NAME", "AZURE_LOCATION",
    )

    # 2) Khởi tạo client quản lý (keyless)
    credential = DefaultAzureCredential()
    client = StorageManagementClient(credential, cfg["AZURE_SUBSCRIPTION_ID"])

    # 3) Tạo storage account (long-running operation -> .result() để chờ xong)
    print(f"Đang tạo storage account '{cfg['STORAGE_ACCOUNT_NAME']}' ...")
    account_poller = client.storage_accounts.begin_create(
        cfg["AZURE_RESOURCE_GROUP"],
        cfg["STORAGE_ACCOUNT_NAME"],
        StorageAccountCreateParameters(
            sku=Sku(name="Standard_LRS"),   # rẻ nhất, nhân bản nội vùng
            kind="StorageV2",               # loại khuyến nghị (hỗ trợ blob/queue/table)
            location=cfg["AZURE_LOCATION"],
            allow_blob_public_access=False,  # tắt truy cập ẩn danh (bảo mật)
        ),
    )
    account = account_poller.result()
    print(f"  -> Đã tạo. Blob endpoint: {account.primary_endpoints.blob}")

    # 4) Tạo container 'documents' để chứa dữ liệu ingest
    print("Đang tạo container 'documents' ...")
    container = client.blob_containers.create(
        cfg["AZURE_RESOURCE_GROUP"],
        cfg["STORAGE_ACCOUNT_NAME"],
        "documents",
        BlobContainer(),                    # mặc định access private
    )
    print(f"  -> Container sẵn sàng: {container.name}")

    # 5) Gợi ý bước tiếp: cấp quyền data-plane bằng role (xem lab 00/02)
    print("\nMẹo: để đọc/ghi blob keyless, gán role 'Storage Blob Data Contributor' (lab 00/02).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
