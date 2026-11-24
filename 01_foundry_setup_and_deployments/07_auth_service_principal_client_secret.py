"""
====================================================================
LAB 01/07 · Auth bằng Service Principal (app registration + client secret)
--------------------------------------------------------------------
Mục tiêu     : app chạy NGOÀI Azure (on-prem / CI-CD) xác thực vào Azure bằng
               danh tính "app" (service principal) rồi đọc Blob Storage — KHÔNG
               nhúng tài khoản cá nhân, KHÔNG dùng API key của storage.
Dịch vụ      : Microsoft Entra ID (service principal) + Azure Blob Storage
Biến .env    : AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, STORAGE_ACCOUNT_NAME
               (tuỳ chọn) BLOB_CONTAINER_NAME
SDK tiền nhiệm: không (azure-identity + azure-storage-blob hiện hành)
Chạy         : uv run 01_foundry_setup_and_deployments/07_auth_service_principal_client_secret.py
Web UI tương đương: Entra ID -> App registrations -> New registration -> Certificates & secrets
                    -> New client secret; rồi Storage -> Access control (IAM) -> gán role cho app.
====================================================================

GHI NHỚ — "App" trong Entra ID = 2 đối tượng sinh ra từ App Registration:
    - Application object : "bản thiết kế" toàn cầu của app (tên, redirect URI...), DUY NHẤT toàn cầu.
    - Service principal  : "thực thể" cục bộ của app trong 1 tenant — CÁI THỰC SỰ được gán quyền.
      => Cấp quyền cho "app" = cấp cho service principal này.
    - Credential: Client ID ("chứng minh thư") + Client Secret / certificate ("chìa khoá").

ĐỐI XỨNG với lab 00/04 (Managed Identity):
    - Service principal (lab NÀY): app NGOÀI Azure; BẠN giữ secret; chạy mọi nơi (on-prem, CI-CD, cloud khác).
    - Managed identity (00/04)    : app TRÊN Azure; Azure giữ credential hộ; không secret.
    - Cả hai khi gán RBAC đều là principal_type='ServicePrincipal'.

Kịch bản điển hình:
    - Web app on-prem cần đọc Blob -> đăng ký app 'my-onprem-reporting-app', tạo secret,
      gán 'Storage Blob Data Reader' cho SP của app, rồi dùng Client ID/Secret để xác thực.
    - CI/CD pipeline (GitHub Actions / Azure DevOps) deploy tài nguyên -> đăng nhập bằng SP, không phải tài khoản người.
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

# ── xác thực bằng service principal ─────────────────────────────
# ClientSecretCredential: xác thực app bằng (tenant_id + client_id + client_secret).
# (DefaultAzureCredential/EnvironmentCredential cũng tự đọc đúng 3 biến AZURE_* này — xem 01/01.)
from azure.identity import ClientSecretCredential

# ── SDK Blob Storage ────────────────────────────────────────────
# azure-storage-blob: BlobServiceClient nhận thẳng credential; SDK tự xin token đúng scope storage.
from azure.storage.blob import BlobServiceClient


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
    cfg = require_env(
        "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET",
        "STORAGE_ACCOUNT_NAME",
    )

    # 1) Danh tính APP (service principal) — không phải người dùng
    credential = ClientSecretCredential(
        tenant_id=cfg["AZURE_TENANT_ID"],
        client_id=cfg["AZURE_CLIENT_ID"],          # = Application (client) ID của app registration
        client_secret=cfg["AZURE_CLIENT_SECRET"],  # = "chìa khoá"; cất kỹ, xoay vòng định kỳ, KHÔNG commit
    )

    # 2) Dùng danh tính app để gọi Blob (SP phải có role 'Storage Blob Data Reader/Contributor')
    account_url = f"https://{cfg['STORAGE_ACCOUNT_NAME']}.blob.core.windows.net"
    service = BlobServiceClient(account_url=account_url, credential=credential)

    # 3) Liệt kê container -> chứng minh app đã xác thực & có quyền data-plane
    print(f"App (SP) {cfg['AZURE_CLIENT_ID']} truy cập {account_url}:")
    containers = list(service.list_containers())
    if not containers:
        print("  (không có container nào — nhưng auth đã THÀNH CÔNG)")
    for c in containers:
        print(f"  - container: {c.name}")

    # 4) (Tuỳ chọn) đọc 1 blob trong container chỉ định
    container_name = os.getenv("BLOB_CONTAINER_NAME")
    if container_name:
        container = service.get_container_client(container_name)
        blobs = list(container.list_blobs())
        print(f"Container '{container_name}' có {len(blobs)} blob:")
        for b in blobs[:10]:
            print(f"  - {b.name} ({b.size} bytes)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
