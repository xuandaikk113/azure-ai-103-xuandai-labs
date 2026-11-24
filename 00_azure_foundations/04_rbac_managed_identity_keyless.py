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

GHI NHỚ — Managed Identity (MI) là gì & 2 loại (System-assigned vs User-assigned):
    - MI là danh tính trong Entra ID do Azure quản lý (không có mật khẩu/secret để lộ).
    - Cả hai loại đều xuất hiện trong RBAC với principal_type = 'ServicePrincipal'. Khác nhau:
        |               | System-assigned            | User-assigned                         |
        | Bản chất      | sinh BÊN TRONG 1 resource  | là tài nguyên Azure ĐỘC LẬP           |
        | Vòng đời      | xoá resource -> MẤT MI     | sống độc lập, resource xoá vẫn còn    |
        | Quan hệ       | 1 : 1 (riêng mỗi resource) | N : M (1 MI gắn cho NHIỀU resource)   |
        | Gán RBAC      | gán LẠI cho từng resource  | gán 1 LẦN, mọi resource gắn nó đều có |
        | Lấy principalId | resource.identity.principal_id (sau khi bật Identity) | identity.principal_id của MI (azure-mgmt-msi) |
    - Ví dụ: 3 Function App cùng đọc 1 Storage:
        * system-assigned -> mỗi app 1 badge riêng -> gán role 3 LẦN.
        * user-assigned   -> tạo 1 MI "id-ai103", gán role 1 LẦN, gắn cho cả 3 app.
    - Chọn: 1 workload đứng riêng -> system-assigned (đơn giản);
            nhiều resource dùng CHUNG quyền / cấp quyền TRƯỚC khi tạo compute (IaC) -> user-assigned.
    - Trong code chọn MI nào khi xác thực:
        * system-assigned -> ManagedIdentityCredential()               (resource chỉ có 1 MI)
        * user-assigned   -> ManagedIdentityCredential(client_id="<client-id-cua-MI>")  (nói rõ dùng cái nào)

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
            principal_type="ServicePrincipal",   # MI (system/user-assigned) đều là ServicePrincipal.
            # QUAN TRỌNG ở đây: MI vừa tạo thường CHƯA replicate -> nếu bỏ principal_type dễ 'PrincipalNotFound'.
            # Đặt rõ 'ServicePrincipal' để bỏ qua bước Azure tự suy từ principal_id (xem chi tiết 00/02).
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
