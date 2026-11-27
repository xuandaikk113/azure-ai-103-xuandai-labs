"""
====================================================================
LAB 07/05 · Translator: dịch text + (ghi chú) dịch document
--------------------------------------------------------------------
Dịch vụ      : Azure AI Translator
Biến .env    : TRANSLATOR_ENDPOINT, TRANSLATOR_API_KEY, TRANSLATOR_REGION
SDK tiền nhiệm: không (azure-ai-translation-text là SDK hiện hành, GA 2.0).
Chạy         : uv run 07_vision_language_and_speech/05_translator_text_and_document_translation.py
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

# ── SDK Translator (text) ───────────────────────────────────────
from azure.ai.translation.text import TextTranslationClient
# Dịch document (hàng loạt, async qua blob): from azure.ai.translation.document import DocumentTranslationClient


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
    cfg = require_env("TRANSLATOR_ENDPOINT", "TRANSLATOR_API_KEY", "TRANSLATOR_REGION")

    client = TextTranslationClient(
        endpoint=cfg["TRANSLATOR_ENDPOINT"],
        credential=AzureKeyCredential(cfg["TRANSLATOR_API_KEY"]),
        region=cfg["TRANSLATOR_REGION"],       # region bắt buộc với key đa vùng
    )
    # ── Alternative KEYLESS (Entra ID, khuyến nghị production) — thay cho AzureKeyCredential ──
    #   from azure.identity import DefaultAzureCredential
    #   client = TextTranslationClient(
    #       endpoint=cfg["TRANSLATOR_ENDPOINT"],
    #       credential=DefaultAzureCredential(),
    #       region=cfg["TRANSLATOR_REGION"],   # vẫn cần region khi dùng token Entra ID
    #   )
    #   (keyless chạy được khi principal có đúng RBAC data-plane role cho service này —
    #    vd Cognitive Services User trên resource Translator; xem lab 00/04)

    # Dịch 1 câu sang NHIỀU ngôn ngữ đích cùng lúc
    result = client.translate(body=["Xin chào, hôm nay bạn thế nào?"], to_language=["en", "ja"])
    for item in result:
        print(f"Phát hiện ngôn ngữ nguồn: {item.detected_language.language}")
        for translation in item.translations:
            print(f"  -> {translation.to}: {translation.text}")

    # Dịch DOCUMENT (hàng loạt) là tác vụ async: DocumentTranslationClient đọc blob nguồn
    # (có SAS) -> ghi blob đích; dùng begin_translation(...).result() để chờ xong.
    print("\nDịch document: dùng DocumentTranslationClient + blob nguồn/đích (xem comment).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
