"""
====================================================================
LAB 09/02 · Monitoring + Online evaluation + Error analysis cho agent
--------------------------------------------------------------------
Dịch vụ      : azure-ai-evaluation (+ Foundry monitoring)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT
SDK tiền nhiệm: không.
Chạy         : uv run 09_observability_and_tracing/02_agent_monitoring_and_online_evaluation.py
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

# ── SDK Evaluation ──────────────────────────────────────────────
# azure-ai-evaluation: các evaluator chấm điểm chất lượng/an toàn, dùng 1 model làm giám khảo.
from azure.ai.evaluation import RelevanceEvaluator, GroundednessEvaluator


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
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_CHAT_DEPLOYMENT",
    )
    model_config = {
        "azure_endpoint": cfg["AZURE_OPENAI_ENDPOINT"],
        "api_key": cfg["AZURE_OPENAI_API_KEY"],
        "azure_deployment": cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"],
        "api_version": cfg["AZURE_OPENAI_API_VERSION"],
    }
    relevance = RelevanceEvaluator(model_config)
    groundedness = GroundednessEvaluator(model_config)

    # Giả lập dữ liệu thu được từ agent đã deploy (online = chấm trên traffic thật)
    samples = [
        {"query": "Thủ đô Việt Nam?", "context": "Hà Nội là thủ đô Việt Nam.",
         "response": "Hà Nội."},
        {"query": "Giá sản phẩm X?", "context": "Sản phẩm X giá 100k.",
         "response": "Sản phẩm X giá 999k."},   # câu trả lời SAI -> điểm thấp
    ]

    print("== Online evaluation + error analysis ==")
    for i, s in enumerate(samples):
        rel = relevance(query=s["query"], response=s["response"], context=s["context"])
        gnd = groundedness(query=s["query"], response=s["response"], context=s["context"])
        print(f"[{i}] relevance={rel}, groundedness={gnd}")
        # Error analysis: gắn cờ mẫu điểm thấp để điều tra
        score = gnd.get("groundedness") if isinstance(gnd, dict) else None
        if score is not None and score < 3:
            print(f"    ⚠ CẢNH BÁO: groundedness thấp -> cần điều tra (có thể 'bịa').")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
