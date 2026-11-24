"""
====================================================================
LAB 00/06 · List / check / remove role assignment — audit & dọn dẹp RBAC
--------------------------------------------------------------------
Mục tiêu     : liệt kê các role assignment ở 1 scope, kiểm tra 1 principal có quyền gì,
               và xoá an toàn 1 assignment (chỉ khi được chỉ định rõ).
Dịch vụ      : Azure RBAC
Biến .env    : AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP
               (tuỳ chọn) RBAC_PRINCIPAL_ID = lọc assignment theo principal
               (tuỳ chọn) RBAC_ASSIGNMENT_NAME_TO_DELETE = tên (GUID) assignment cần xoá
SDK tiền nhiệm: không (azure-mgmt-authorization hiện hành)
Chạy         : uv run 00_azure_foundations/06_rbac_list_check_remove.py
Web UI tương đương: Portal -> scope -> Access control (IAM) -> Role assignments (xem/xoá).
====================================================================

GHI NHỚ:
    - list_for_scope KHÔNG tự trả về assignment thừa kế từ cấp trên trừ khi lọc atScope.
      Mặc định ở đây liệt kê mọi assignment nhìn thấy tại scope (gồm kế thừa).
    - Xoá assignment cần 'name' (GUID) của nó — lấy từ bước liệt kê.
    - An toàn: chỉ xoá khi có RBAC_ASSIGNMENT_NAME_TO_DELETE, tránh xoá nhầm hàng loạt.
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

# ── xác thực ────────────────────────────────────────────────────
from azure.identity import DefaultAzureCredential

# ── SDK RBAC ────────────────────────────────────────────────────
from azure.mgmt.authorization import AuthorizationManagementClient


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def role_name_of(client: AuthorizationManagementClient, scope: str, role_def_id: str) -> str:
    """Đổi role_definition_id (GUID path) sang tên role cho dễ đọc."""
    try:
        return client.role_definitions.get_by_id(role_def_id).role_name
    except Exception:
        return role_def_id.rsplit("/", 1)[-1]


def main() -> None:
    cfg = require_env("AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP")
    principal_filter = os.getenv("RBAC_PRINCIPAL_ID")
    to_delete = os.getenv("RBAC_ASSIGNMENT_NAME_TO_DELETE")

    credential = DefaultAzureCredential()
    client = AuthorizationManagementClient(credential, cfg["AZURE_SUBSCRIPTION_ID"])
    scope = f"/subscriptions/{cfg['AZURE_SUBSCRIPTION_ID']}/resourceGroups/{cfg['AZURE_RESOURCE_GROUP']}"

    # 1) Liệt kê (tuỳ chọn lọc theo principal). filter='principalId eq {id}' khi cần.
    flt = f"principalId eq '{principal_filter}'" if principal_filter else None
    assignments = list(client.role_assignments.list_for_scope(scope, filter=flt))
    print(f"Tìm thấy {len(assignments)} role assignment ở scope RG"
          + (f" (lọc principal {principal_filter})" if principal_filter else "") + ":")
    for a in assignments:
        print(f"  - name={a.name}  role={role_name_of(client, scope, a.role_definition_id)}  "
              f"principal={a.principal_id}  type={a.principal_type}")

    # 2) Xoá an toàn: chỉ khi được chỉ định đúng 1 assignment theo name
    if to_delete:
        client.role_assignments.delete(scope, to_delete)
        print(f"Đã xoá assignment name={to_delete}.")
    else:
        print("(Không xoá gì: đặt RBAC_ASSIGNMENT_NAME_TO_DELETE=<name> để xoá đúng 1 assignment.)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
