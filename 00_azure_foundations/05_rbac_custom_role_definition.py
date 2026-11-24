"""
====================================================================
LAB 00/05 · Custom role definition — khi built-in role không vừa
--------------------------------------------------------------------
Mục tiêu     : tạo 1 CUSTOM ROLE với tập actions/dataActions riêng, rồi (tuỳ chọn)
               gán cho principal. Dùng khi không có built-in role khớp đúng nhu cầu.
Dịch vụ      : Azure RBAC (role definition tuỳ biến)
Biến .env    : AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP
               (tuỳ chọn) RBAC_PRINCIPAL_ID = gán luôn custom role cho principal này
SDK tiền nhiệm: không (azure-mgmt-authorization hiện hành)
Chạy         : uv run 00_azure_foundations/05_rbac_custom_role_definition.py
Web UI tương đương: Portal -> Subscription/RG -> Access control (IAM) -> Add -> Add custom role.
====================================================================

GHI NHỚ — control plane vs data plane trong 1 role:
    - actions / notActions       : quyền MANAGEMENT (ARM) — tạo/sửa/xoá/đọc cấu hình resource.
    - dataActions / notDataActions: quyền DATA — thao tác DỮ LIỆU bên trong resource
                                    (vd gọi inference, đọc blob, query index). Keyless cần cái này.
    - assignableScopes           : custom role chỉ gán được trong các scope liệt kê ở đây.
    - roleType = 'CustomRole'.
GHI NHỚ: ưu tiên built-in role (lab 03) trước; chỉ tạo custom khi thật sự cần quyền đặc thù.
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

# ── xác thực (cần Owner / User Access Administrator) ─────────────
from azure.identity import DefaultAzureCredential

# ── SDK RBAC ────────────────────────────────────────────────────
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import (
    RoleDefinition,                 # mô tả 1 role (tên, quyền, scope gán được)
    Permission,                     # 1 nhóm actions/dataActions
    RoleAssignmentCreateParameters,
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
    cfg = require_env("AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP")
    principal_id = os.getenv("RBAC_PRINCIPAL_ID")        # có thì gán luôn, không có thì chỉ tạo role

    credential = DefaultAzureCredential()
    client = AuthorizationManagementClient(credential, cfg["AZURE_SUBSCRIPTION_ID"])

    rg_scope = f"/subscriptions/{cfg['AZURE_SUBSCRIPTION_ID']}/resourceGroups/{cfg['AZURE_RESOURCE_GROUP']}"

    # 1) Định nghĩa custom role: đọc cấu hình Cognitive Services + gọi inference OpenAI,
    #    nhưng KHÔNG cho sửa/xoá resource (hẹp hơn Contributor).
    role_def_name = str(uuid.uuid4())   # name của role definition là 1 GUID
    role = RoleDefinition(
        role_name="AI-103 Inference Reader (custom)",
        description="Đọc cấu hình Cognitive Services và gọi inference Azure OpenAI; không sửa/xoá.",
        role_type="CustomRole",
        permissions=[
            Permission(
                actions=[                                   # control plane (chỉ đọc)
                    "Microsoft.CognitiveServices/accounts/read",
                    "Microsoft.CognitiveServices/accounts/deployments/read",
                ],
                data_actions=[                              # data plane (gọi model)
                    "Microsoft.CognitiveServices/accounts/OpenAI/deployments/chat/completions/action",
                ],
                not_actions=[],
                not_data_actions=[],
            )
        ],
        assignable_scopes=[rg_scope],                       # chỉ gán được trong RG này
    )

    # 2) Tạo/cập nhật role definition tại scope RG
    created = client.role_definitions.create_or_update(rg_scope, role_def_name, role)
    print(f"Đã tạo custom role '{created.role_name}' -> {created.id}")

    # 3) (Tuỳ chọn) gán custom role cho principal
    if principal_id:
        assignment = client.role_assignments.create(
            rg_scope,
            str(uuid.uuid4()),
            RoleAssignmentCreateParameters(
                role_definition_id=created.id,
                principal_id=principal_id,
                principal_type="User",
            ),
        )
        print(f"Đã gán custom role cho principal. Assignment id: {assignment.id}")
    else:
        print("(Bỏ qua gán: đặt RBAC_PRINCIPAL_ID trong .env để gán luôn.)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
