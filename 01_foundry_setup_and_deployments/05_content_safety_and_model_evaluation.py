"""
====================================================================
LAB 01/05 · Content Safety + Model Evaluation
--------------------------------------------------------------------
Dịch vụ      : Azure AI Content Safety + azure-ai-evaluation
Biến .env    : CONTENT_SAFETY_ENDPOINT, CONTENT_SAFETY_API_KEY
               (evaluator cần thêm: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
                AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT)
               (ghi đè RAI policy cần thêm: AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP,
                AOAI_ACCOUNT_NAME; optional AZURE_OPENAI_CHAT_DEPLOYMENT để gắn policy)
SDK tiền nhiệm: Content Moderator (đã retire) -> Content Safety.
Chạy         : uv run 01_foundry_setup_and_deployments/05_content_safety_and_model_evaluation.py
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

# ── xác thực bằng key (Content Safety hỗ trợ key hoặc keyless) ──
from azure.core.credentials import AzureKeyCredential

# ── SDK Content Safety ──────────────────────────────────────────
# azure-ai-contentsafety: kiểm duyệt text/ảnh theo 4 nhóm hại + mức severity.
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


# Thang severity Content Safety: 0 (an toàn) / 2 (thấp) / 4 (trung bình) / 6 (cao).
# Coi là "đáng chặn" khi severity >= 4 (trung bình trở lên).
MEDIUM_SEVERITY_THRESHOLD = 4


def moderate_text(endpoint: str, key: str) -> list[tuple[str, int]]:
    """Phân tích an toàn nội dung: in severity theo từng category.

    Trả về danh sách (category, severity) của các nhóm đạt ngưỡng trung bình/cao.
    """
    client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
    text = "Hôm nay trời đẹp, mình đi dạo công viên."   # đổi thành nội dung cần kiểm
    result = client.analyze_text(AnalyzeTextOptions(text=text))

    print(f"Văn bản: {text!r}")
    flagged: list[tuple[str, int]] = []
    # 4 category: Hate, SelfHarm, Sexual, Violence
    for item in result.categories_analysis:
        print(f"  - {item.category}: severity={item.severity}")
        if item.severity >= MEDIUM_SEVERITY_THRESHOLD:
            flagged.append((item.category, item.severity))
    return flagged


def handle_moderation_result(flagged: list[tuple[str, int]]) -> None:
    """Xử lý khi phát hiện nội dung severity TRUNG BÌNH hoặc CAO.

    Thực tế: chặn request, ghi log/alert, hoặc chuyển người kiểm duyệt review.
    """
    if not flagged:
        print("  => An toàn: không category nào đạt ngưỡng trung bình (severity >= 4).")
        return
    print("  => CHẶN nội dung — category vượt ngưỡng:")
    for category, severity in flagged:
        level = "CAO" if severity >= 6 else "TRUNG BÌNH"
        print(f"       - {category}: severity={severity} ({level})")
    # Hành động thật tuỳ pipeline, ví dụ dừng xử lý:
    # raise RuntimeError("Nội dung vi phạm chính sách an toàn.")


def evaluate_relevance(query: str, response: str, context: str) -> None:
    """Chạy 1 evaluator (RelevanceEvaluator) — cần 1 model làm 'giám khảo'."""
    # import tại chỗ để phần Content Safety vẫn chạy nếu chưa cấu hình OpenAI.
    from azure.ai.evaluation import RelevanceEvaluator

    model_config = {
        "azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
        "api_key": os.environ["AZURE_OPENAI_API_KEY"],
        "azure_deployment": os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"],
        "api_version": os.environ["AZURE_OPENAI_API_VERSION"],
    }
    relevance = RelevanceEvaluator(model_config)
    score = relevance(query=query, response=response, context=context)
    print("Relevance:", score)   # thường trả dict gồm điểm số + lý do


def override_azure_openai_content_filter() -> None:
    """Ghi đè bộ lọc nội dung (content filter) MẶC ĐỊNH của Azure OpenAI bằng CODE.

    Mặc định Azure OpenAI gắn RAI policy 'Microsoft.Default' — chặn severity Medium + High
    cho cả 4 category. Trên Web UI chỉnh được ngưỡng; dưới đây là cách làm bằng CODE qua
    Azure Resource Manager (control-plane HTTP API) — dùng trong CI/CD, lặp lại được.
    """
    # import tại chỗ: phần Content Safety phía trên vẫn chạy nếu chưa cấu hình mgmt.
    # azure-mgmt-cognitiveservices: quản lý tài nguyên Azure OpenAI (control plane / ARM).
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
    from azure.mgmt.cognitiveservices.models import (
        RaiPolicy, RaiPolicyProperties, RaiPolicyContentFilter,
    )

    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    resource_group = os.environ["AZURE_RESOURCE_GROUP"]
    account_name = os.environ["AOAI_ACCOUNT_NAME"]                 # tên tài nguyên Azure OpenAI
    deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")    # optional: để gắn policy vào deployment

    management_client = CognitiveServicesManagementClient(
        DefaultAzureCredential(), subscription_id,
    )

    # Mỗi RaiPolicyContentFilter = cấu hình cho 1 category, 1 chiều (Prompt HOẶC Completion).
    # severity_threshold: 'Low' | 'Medium' | 'High' — CHẶN khi severity >= ngưỡng này.
    #   -> đặt 'High' = CHỈ chặn mức cao nhất (nới lỏng so với mặc định 'Medium').
    content_filters = []
    for category in ("Hate", "Sexual", "Violence", "SelfHarm"):
        for source in ("Prompt", "Completion"):           # áp cho CẢ input lẫn output
            content_filters.append(
                RaiPolicyContentFilter(
                    name=category,
                    blocking=True,             # True = chặn; False = chỉ gắn nhãn (annotate), không chặn
                    enabled=True,
                    severity_threshold="High",  # nới: chỉ chặn severity cao
                    source=source,
                )
            )

    policy = RaiPolicy(
        properties=RaiPolicyProperties(
            base_policy_name="Microsoft.Default",   # kế thừa policy mặc định rồi ghi đè
            mode="Blocking",                         # 'Blocking' | 'Asynchronous_filter' | 'Default'
            content_filters=content_filters,
        )
    )
    created = management_client.rai_policies.create_or_update(
        resource_group_name=resource_group,
        account_name=account_name,
        rai_policy_name="ai103-relaxed-highonly",
        rai_policy=policy,
    )
    print(f"Đã tạo/cập nhật RAI policy: {created.name}")

    # Để ÁP DỤNG: cập nhật deployment với properties.rai_policy_name = tên policy ở trên
    # (begin_create_or_update deployment — xem lab 01/02). Một policy có thể gắn cho nhiều deployment.
    if deployment_name:
        print(f"  Gắn vào deployment '{deployment_name}': đặt rai_policy_name='{created.name}' (xem lab 01/02).")

    # ── Cách THAY THẾ: gọi REST THUẦN (không cần SDK mgmt) ──────────────────────────
    # PUT https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}
    #     /providers/Microsoft.CognitiveServices/accounts/{account}/raiPolicies/{policyName}
    #     ?api-version=2025-06-01
    # Header: Authorization: Bearer <token scope https://management.azure.com/.default>
    # Body  : {"properties": {"basePolicyName": "Microsoft.Default", "mode": "Blocking",
    #          "contentFilters": [{"name": "Hate", "blocking": true, "enabled": true,
    #                              "severityThreshold": "High", "source": "Prompt"}, ...]}}


def main() -> None:
    cfg = require_env("CONTENT_SAFETY_ENDPOINT", "CONTENT_SAFETY_API_KEY")

    # 1) Content Safety: phân tích + XỬ LÝ khi severity trung bình/cao
    flagged = moderate_text(cfg["CONTENT_SAFETY_ENDPOINT"], cfg["CONTENT_SAFETY_API_KEY"])
    handle_moderation_result(flagged)

    # 2) Evaluation (bỏ qua nếu chưa cấu hình model giám khảo)
    print("\n== Đánh giá chất lượng (RelevanceEvaluator) ==")
    if all(os.getenv(k) for k in (
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_CHAT_DEPLOYMENT",
    )):
        evaluate_relevance(
            query="Thủ đô Việt Nam là gì?",
            response="Thủ đô Việt Nam là Hà Nội.",
            context="Hà Nội là thủ đô của Việt Nam.",
        )
    else:
        print("  (bỏ qua: chưa cấu hình AZURE_OPENAI_* cho model giám khảo)")

    # 3) (tuỳ chọn) Ghi đè content filter MẶC ĐỊNH của Azure OpenAI bằng code (RAI policy)
    print("\n== Ghi đè content filter (RAI policy) qua control-plane API ==")
    if all(os.getenv(k) for k in (
        "AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP", "AOAI_ACCOUNT_NAME",
    )):
        override_azure_openai_content_filter()
    else:
        print("  (bỏ qua: cần AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AOAI_ACCOUNT_NAME)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
