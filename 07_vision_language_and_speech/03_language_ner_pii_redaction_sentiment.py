"""
====================================================================
LAB 07/03 · Language: NER + PII redaction + Sentiment (opinion mining)
--------------------------------------------------------------------
Dịch vụ      : Azure AI Language (Text Analytics)
Biến .env    : LANGUAGE_ENDPOINT, LANGUAGE_API_KEY
SDK tiền nhiệm: azure-cognitiveservices-language-textanalytics (cũ) -> azure-ai-textanalytics.
Chạy         : uv run 07_vision_language_and_speech/03_language_ner_pii_redaction_sentiment.py
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

# ── SDK Text Analytics ──────────────────────────────────────────
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
    cfg = require_env("LANGUAGE_ENDPOINT", "LANGUAGE_API_KEY")
    client = TextAnalyticsClient(cfg["LANGUAGE_ENDPOINT"], AzureKeyCredential(cfg["LANGUAGE_API_KEY"]))

    docs = ["Ông Nam gọi số 0901234567, email nam@example.com, dịch vụ rất tuyệt vời."]

    # 1) NER: nhận diện thực thể (người, địa điểm, tổ chức...)
    print("== NER ==")
    for doc in client.recognize_entities(docs):
        for ent in doc.entities:
            print(f"  - {ent.text} ({ent.category})")

    # 2) PII: phát hiện + CHE thông tin nhạy cảm; redacted_text đã bị che
    print("\n== PII redaction ==")
    for doc in client.recognize_pii_entities(docs):
        print("  Redacted:", doc.redacted_text)

    # 3) Sentiment + opinion mining (cảm xúc theo câu + khía cạnh)
    print("\n== Sentiment ==")
    for doc in client.analyze_sentiment(docs, show_opinion_mining=True):
        print(f"  Tổng thể: {doc.sentiment}")
        for sentence in doc.sentences:
            print(f"    câu: {sentence.sentiment} ({sentence.text})")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
