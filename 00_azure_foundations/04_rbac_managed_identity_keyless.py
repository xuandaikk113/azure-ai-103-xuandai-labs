"""
====================================================================
LAB 00/04 · RBAC cho Managed Identity — để app/agent gọi service KEYLESS
--------------------------------------------------------------------
Mục tiêu     : gán built-in role cho 1 MANAGED IDENTITY (MI) để ứng dụng dùng
               DefaultAzureCredential gọi AI service mà KHÔNG cần API key.
Dịch vụ      : Azure RBAC + Managed Identity (Entra ID)
Biến .env    : AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, MI_PRINCIPAL_ID, RBAC_ROLE_NAME
SDK tiền nhiệm: không (azure-mgmt-authorization hiện hành)
Chạy         : uv run 00_azure_foundations/04_rbac_managed_identity_keyless.py
Web UI tương đương: Portal -> Resource -> Access control (IAM) -> Add role assignment
                    -> Assign access to: Managed identity -> chọn MI.
====================================================================

GHI NHỚ — Managed Identity (MI) là gì & 2 loại:
    - MI là danh tính trong Entra ID do Azure quản lý (không có mật khẩu/secret để lộ).
    - System-assigned : gắn CHẶT vào 1 resource (App Service, VM, Function...). Xoá resource -> mất MI.
        * Lấy principalId: bật Identity trên resource -> resource.identity.principal_id
    - User-assigned   : resource độc lập, GẮN được cho NHIỀU resource dùng chung.
        * Lấy principalId: tạo identity (azure-mgmt-msi) -> identity.principal_id
    - Cả hai đều xuất hiện trong RBAC với principal_type = 'ServicePrincipal'.

GHI NHỚ — vì sao keyless cần RBAC:
    DefaultAzureCredential lấy token của MI, nhưng token chỉ gọi được service khi MI
    ĐÃ có role data-plane phù hợp (vd 'Cognitive Services OpenAI User' để gọi chat).
    -> Không gán role = lỗi 401/403 dù code đúng.
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import uuid

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── xác thực (cần Owner / User Access Administrator để gán RBAC) ──
from azure.identity import DefaultAzureCredential

# ── SDK RBAC ────────────────────────────────────────────────────
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters


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
        "AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP",
        "MI_PRINCIPAL_ID", "RBAC_ROLE_NAME",       # MI_PRINCIPAL_ID = object/principal id của managed identity
    )

    credential = DefaultAzureCredential()
    client = AuthorizationManagementClient(credential, cfg["AZURE_SUBSCRIPTION_ID"])

    # Scope = RG (đổi sang resource cụ thể để hẹp hơn — xem lab 03).
    scope = f"/subscriptions/{cfg['AZURE_SUBSCRIPTION_ID']}/resourceGroups/{cfg['AZURE_RESOURCE_GROUP']}"

    # 1) Tra role (vd 'Cognitive Services OpenAI User' cho inference keyless)
    role_name = cfg["RBAC_ROLE_NAME"]
    role_defs = list(client.role_definitions.list(scope, filter=f"roleName eq '{role_name}'"))
    if not role_defs:
        sys.exit(f"[LỖI] Không tìm thấy role '{role_name}'.")
    role_def_id = role_defs[0].id

    # 2) Gán role cho MANAGED IDENTITY — khác lab 02 ở principal_type='ServicePrincipal'
    assignment = client.role_assignments.create(
        scope,
        str(uuid.uuid4()),
        RoleAssignmentCreateParameters(
            role_definition_id=role_def_id,
            principal_id=cfg["MI_PRINCIPAL_ID"],
            principal_type="ServicePrincipal",   # MI (system/user-assigned) đều là ServicePrincipal
        ),
    )
    print(f"Đã gán '{role_name}' cho managed identity. Assignment id: {assignment.id}")
    print("Giờ app chạy dưới MI này có thể DefaultAzureCredential() gọi service keyless.")
    print("(Có thể mất vài phút để quyền có hiệu lực.)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
