"""
====================================================================
LAB 07/04 · CLU (intent/entity) + Summarization (extractive & abstractive)
--------------------------------------------------------------------
Dịch vụ      : Azure AI Language (CLU + Text Analytics summarization)
Biến .env    : LANGUAGE_ENDPOINT, LANGUAGE_API_KEY, CLU_PROJECT_NAME, CLU_DEPLOYMENT_NAME
SDK tiền nhiệm: LUIS -> CLU (Conversational Language Understanding).
Chạy         : uv run 07_vision_language_and_speech/04_language_clu_intent_and_summarization.py
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

# ── xác thực ────────────────────────────────────────────────────
from azure.core.credentials import AzureKeyCredential

# ── SDK ─────────────────────────────────────────────────────────
# ConversationAnalysisClient: gọi mô hình CLU (intent + entity).
from azure.ai.language.conversations import ConversationAnalysisClient
# TextAnalyticsClient: tóm tắt văn bản (extractive/abstractive).
from azure.ai.textanalytics import TextAnalyticsClient


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
        "LANGUAGE_ENDPOINT", "LANGUAGE_API_KEY",
        "CLU_PROJECT_NAME", "CLU_DEPLOYMENT_NAME",
    )
    credential = AzureKeyCredential(cfg["LANGUAGE_API_KEY"])
    # ── Alternative KEYLESS (Entra ID, khuyến nghị production) — thay cho AzureKeyCredential ──
    #   from azure.identity import DefaultAzureCredential
    #   credential = DefaultAzureCredential()
    #   clu = ConversationAnalysisClient(cfg["LANGUAGE_ENDPOINT"], credential)
    #   ta = TextAnalyticsClient(cfg["LANGUAGE_ENDPOINT"], credential)
    #   (keyless chạy được khi principal có đúng RBAC data-plane role cho service này —
    #    vd Cognitive Services User trên resource Language; xem lab 00/04)

    # 1) CLU: phân tích intent + entity của 1 câu người dùng
    clu = ConversationAnalysisClient(cfg["LANGUAGE_ENDPOINT"], credential)
    result = clu.analyze_conversation(task={
        "kind": "Conversation",
        "analysisInput": {"conversationItem": {
            "id": "1", "participantId": "user", "text": "Đặt vé bay đi Đà Nẵng ngày mai",
        }},
        "parameters": {
            "projectName": cfg["CLU_PROJECT_NAME"],
            "deploymentName": cfg["CLU_DEPLOYMENT_NAME"],
        },
    })
    prediction = result["result"]["prediction"]
    print("Top intent:", prediction["topIntent"])
    print("Entities:", [(e["category"], e["text"]) for e in prediction["entities"]])

    # 2) Summarization: 2 kiểu (extractive = trích câu, abstractive = viết lại)
    ta = TextAnalyticsClient(cfg["LANGUAGE_ENDPOINT"], credential)
    docs = ["Azure AI Language cung cấp NER, PII, phân tích cảm xúc, tóm tắt và CLU. "
            "Nó giúp xây dựng ứng dụng hiểu ngôn ngữ tự nhiên nhanh chóng."]

    extract_poller = ta.begin_extract_summary(docs)
    for doc in extract_poller.result():
        print("\nExtractive:", " ".join(s.text for s in doc.sentences))

    abstract_poller = ta.begin_abstract_summary(docs)
    for doc in abstract_poller.result():
        print("Abstractive:", " ".join(s.text for s in doc.summaries))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
