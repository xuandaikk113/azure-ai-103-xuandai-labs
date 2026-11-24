"""
====================================================================
LAB 00/03 · RBAC scopes & built-in AI roles — gán đúng phạm vi (least privilege)
--------------------------------------------------------------------
Mục tiêu     : hiểu 4 cấp SCOPE và chọn built-in role AI phù hợp, rồi gán ở
               scope hẹp nhất đủ dùng (least privilege).
Dịch vụ      : Azure RBAC (Microsoft.Authorization, ARM)
Biến .env    : AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, RBAC_PRINCIPAL_ID, RBAC_ROLE_NAME
               (tuỳ chọn) RBAC_SCOPE_LEVEL = subscription | rg | resource
               (tuỳ chọn) RBAC_TARGET_RESOURCE_ID = id resource cụ thể khi scope=resource
SDK tiền nhiệm: không (azure-mgmt-authorization là SDK hiện hành cho RBAC)
Chạy         : uv run 00_azure_foundations/03_rbac_scopes_and_builtin_roles.py
Web UI tương đương: Portal -> (Subscription | RG | Resource) -> Access control (IAM) -> Add role assignment.
====================================================================

GHI NHỚ — 4 cấp SCOPE (quyền THỪA KẾ xuống dưới, không kế lên trên):
    Management group  >  Subscription  >  Resource group  >  Resource
    Gán càng cao càng rộng. Nguyên tắc least privilege: gán ở cấp THẤP NHẤT đủ dùng.

GHI NHỚ — built-in role AI hay dùng (đủ cho AI-103, không cần custom role):
    | Role                              | Cho ai / làm gì                                   |
    |-----------------------------------|---------------------------------------------------|
    | Azure AI Developer                | Dev: tạo/chạy project, agent, deployment (Foundry)|
    | Cognitive Services User           | Gọi AI service bằng KEY (đọc key)                 |
    | Cognitive Services OpenAI User    | Gọi Azure OpenAI inference (chat/embedding) keyless|
    | Cognitive Services OpenAI Contributor | Tạo/sửa deployment, fine-tune                 |
    | Search Index Data Reader          | Query dữ liệu trong index (RAG read)              |
    | Search Index Data Contributor     | Ghi/ingest tài liệu vào index                     |
    | Storage Blob Data Reader/Contributor | Đọc/ghi blob (ingest RAG, output)              |
    -> keyless (DefaultAzureCredential) chỉ chạy được khi principal có role data-plane đúng ở trên.
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import uuid                      # role assignment cần 1 GUID làm tên

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── xác thực keyless (cần Owner / User Access Administrator để gán RBAC) ──
from azure.identity import DefaultAzureCredential

# ── SDK quản lý Authorization (RBAC) ────────────────────────────
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


def build_scope(level: str, sub: str, rg: str, resource_id: str | None) -> str:
    """Dựng chuỗi scope theo cấp mong muốn. Scope chỉ là 1 chuỗi đường dẫn ARM."""
    if level == "subscription":
        # Rộng: role áp cho MỌI resource trong subscription.
        return f"/subscriptions/{sub}"
    if level == "rg":
        # Trung bình: áp cho mọi resource trong resource group.
        return f"/subscriptions/{sub}/resourceGroups/{rg}"
    if level == "resource":
        # Hẹp nhất (least privilege): chỉ đúng 1 resource.
        if not resource_id:
            sys.exit("[THIẾU] scope=resource cần RBAC_TARGET_RESOURCE_ID (id đầy đủ của resource).")
        return resource_id
    sys.exit(f"[LỖI] RBAC_SCOPE_LEVEL không hợp lệ: {level} (dùng subscription|rg|resource).")


def main() -> None:
    cfg = require_env(
        "AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP",
        "RBAC_PRINCIPAL_ID", "RBAC_ROLE_NAME",
    )
    level = os.getenv("RBAC_SCOPE_LEVEL", "rg")          # mặc định RG
    resource_id = os.getenv("RBAC_TARGET_RESOURCE_ID")

    credential = DefaultAzureCredential()
    client = AuthorizationManagementClient(credential, cfg["AZURE_SUBSCRIPTION_ID"])

    # 1) Chọn scope theo cấp -> quyết định phạm vi ảnh hưởng của quyền
    scope = build_scope(level, cfg["AZURE_SUBSCRIPTION_ID"], cfg["AZURE_RESOURCE_GROUP"], resource_id)
    print(f"Scope ({level}): {scope}")

    # 2) Tra role_definition_id theo tên role (các role ở bảng GHI NHỚ trên)
    role_name = cfg["RBAC_ROLE_NAME"]
    role_defs = list(client.role_definitions.list(scope, filter=f"roleName eq '{role_name}'"))
    if not role_defs:
        sys.exit(f"[LỖI] Không tìm thấy role '{role_name}' ở scope này.")
    role_def_id = role_defs[0].id

    # 3) Gán (principal + role) vào scope đã chọn
    assignment = client.role_assignments.create(
        scope,
        str(uuid.uuid4()),
        RoleAssignmentCreateParameters(
            role_definition_id=role_def_id,
            principal_id=cfg["RBAC_PRINCIPAL_ID"],
            principal_type="User",       # 'ServicePrincipal' nếu là app/managed identity (xem lab 04)
        ),
    )
    print(f"Đã gán '{role_name}' @ {level}. Assignment id: {assignment.id}")
    print("Mẹo least privilege: ưu tiên scope=resource; chỉ lên rg/subscription khi thật sự cần.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
