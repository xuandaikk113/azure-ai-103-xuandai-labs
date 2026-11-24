"""
====================================================================
LAB 00/02 · Grant RBAC — gán role cho principal bằng code
--------------------------------------------------------------------
Dịch vụ      : Azure RBAC (Microsoft.Authorization, ARM)
Biến .env    : AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, RBAC_PRINCIPAL_ID, RBAC_ROLE_NAME
SDK tiền nhiệm: không (azure-mgmt-authorization là SDK hiện hành cho RBAC)
Chạy         : uv run 00_azure_foundations/02_grant_rbac_role_assignment.py
Web UI tương đương: Portal -> resource/RG -> Access control (IAM) -> Add role assignment.
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import uuid                      # role assignment cần 1 GUID làm tên (name)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── xác thực keyless ────────────────────────────────────────────
# Cần quyền quản lý quyền (vd role "Owner" hoặc "User Access Administrator") để gán RBAC.
from azure.identity import DefaultAzureCredential

# ── SDK quản lý Authorization (RBAC) ────────────────────────────
# azure-mgmt-authorization: liệt kê role definition & tạo role assignment.
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
    # 1) Đọc cấu hình
    cfg = require_env(
        "AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP",
        "RBAC_PRINCIPAL_ID", "RBAC_ROLE_NAME",
    )

    # 2) Client quản lý RBAC
    credential = DefaultAzureCredential()
    client = AuthorizationManagementClient(credential, cfg["AZURE_SUBSCRIPTION_ID"])

    # 3) Scope = RG (quyền sẽ thừa kế xuống mọi resource trong RG).
    #    Muốn hẹp hơn: trỏ scope tới 1 resource cụ thể (least privilege).
    scope = (
        f"/subscriptions/{cfg['AZURE_SUBSCRIPTION_ID']}"
        f"/resourceGroups/{cfg['AZURE_RESOURCE_GROUP']}"
    )

    # 4) Tra role_definition_id theo TÊN role (vd 'Cognitive Services User')
    role_name = cfg["RBAC_ROLE_NAME"]
    role_defs = list(
        client.role_definitions.list(scope, filter=f"roleName eq '{role_name}'")
    )
    if not role_defs:
        sys.exit(f"[LỖI] Không tìm thấy role '{role_name}'.")
    role_def_id = role_defs[0].id
    print(f"Role '{role_name}' -> {role_def_id}")

    # 5) Tạo role assignment: gắn (principal + role) vào scope
    assignment = client.role_assignments.create(
        scope,
        str(uuid.uuid4()),               # name: GUID bất kỳ, duy nhất
        RoleAssignmentCreateParameters(
            # --- 2 field BẮT BUỘC ---
            role_definition_id=role_def_id,
            principal_id=cfg["RBAC_PRINCIPAL_ID"],   # objectId của user / group / SP / managed identity
            # --- field TÙY CHỌN (nhưng NÊN đặt) ---
            principal_type="User",       # 'User' | 'Group' | 'ServicePrincipal' (app & MI đều là ServicePrincipal).
            # Bỏ qua -> Azure TỰ SUY từ principal_id. Nhưng với principal VỪA tạo (Entra chưa replicate xong),
            # bước suy luận dễ fail -> lỗi 'PrincipalNotFound'. Đặt rõ principal_type để BỎ QUA tra cứu đó -> chắc ăn hơn.
            # (Field optional khác của RoleAssignmentCreateParameters: description; condition + condition_version cho ABAC.)
        ),
    )
    print(f"Đã gán quyền. Assignment id: {assignment.id}")
    print("(Quyền có thể mất vài phút để có hiệu lực.)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
