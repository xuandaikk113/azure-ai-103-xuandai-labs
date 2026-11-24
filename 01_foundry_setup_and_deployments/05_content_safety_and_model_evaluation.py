"""
====================================================================
LAB 01/05 · Content Safety + Model Evaluation
--------------------------------------------------------------------
Dịch vụ      : Azure AI Content Safety + azure-ai-evaluation
Biến .env    : CONTENT_SAFETY_ENDPOINT, CONTENT_SAFETY_API_KEY
               (evaluator cần thêm: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
                AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT)
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


def moderate_text(endpoint: str, key: str) -> None:
    """Phân tích an toàn nội dung: in severity theo từng category."""
    client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
    text = "Hôm nay trời đẹp, mình đi dạo công viên."   # đổi thành nội dung cần kiểm
    result = client.analyze_text(AnalyzeTextOptions(text=text))

    print(f"Văn bản: {text!r}")
    # severity nằm trong thang 0 (an toàn) / 2 / 4 / 6 (nặng nhất)
    for item in result.categories_analysis:
        print(f"  - {item.category}: severity={item.severity}")
    # 4 category: Hate, SelfHarm, Sexual, Violence


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


def main() -> None:
    cfg = require_env("CONTENT_SAFETY_ENDPOINT", "CONTENT_SAFETY_API_KEY")

    # 1) Content Safety
    moderate_text(cfg["CONTENT_SAFETY_ENDPOINT"], cfg["CONTENT_SAFETY_API_KEY"])

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


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
