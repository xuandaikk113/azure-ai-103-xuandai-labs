"""
====================================================================
LAB 02/01 · Chat completions "classic" (AzureOpenAI) — file đối chiếu alternative
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT
SDK tiền nhiệm: openai<1.0 (openai.ChatCompletion.create) -> lớp AzureOpenAI.
Lưu ý        : File này CỐ TÌNH giữ AzureOpenAI (vẫn hỗ trợ, chưa deprecated) làm bản "classic".
               Cách KHUYẾN NGHỊ hiện nay: OpenAI client + base_url /openai/v1/ (bỏ api_version) — xem file khác.
Chạy         : uv run 02_genai_chat_alternatives/01_chat_azure_openai_sdk_completions.py
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

# ── SDK ─────────────────────────────────────────────────────────
from openai import AzureOpenAI   # client đồng bộ; bản async là AsyncAzureOpenAI


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

    client = AzureOpenAI(
        azure_endpoint=cfg["AZURE_OPENAI_ENDPOINT"],
        api_key=cfg["AZURE_OPENAI_API_KEY"],
        api_version=cfg["AZURE_OPENAI_API_VERSION"],
    )
    # ── Alternative KEYLESS (Entra ID, khuyến nghị production) — thay cho api_key ──
    #   from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    #   token_provider = get_bearer_token_provider(
    #       DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")  # scope AzureOpenAI classic
    #   client = AzureOpenAI(azure_endpoint=..., api_version=..., azure_ad_token_provider=token_provider)

    # messages: danh sách lượt hội thoại. Vai trò: system (chỉ dẫn) / user / assistant.
    resp = client.chat.completions.create(
        model=cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"],   # 'model' = tên DEPLOYMENT
        messages=[
            {"role": "system", "content": "Bạn là trợ lý tiếng Việt, trả lời ngắn gọn."},
            {"role": "user", "content": "Giải thích RAG trong 1 câu."},
        ],
        temperature=0.7,     # optional — độ sáng tạo (0 = chắc chắn, 1 = đa dạng); mặc định 1.0
    )

    print("Trả lời:", resp.choices[0].message.content)
    print(f"Token: {resp.usage.total_tokens}")

    # ── Alternative · cùng tác vụ bằng RESPONSES API (chuẩn mới, nền agentic, xem lab 02/02) ──
    #   r = client.responses.create(
    #       model=cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"],
    #       input="Giải thích RAG trong 1 câu.",                          # thay cho 'messages'
    #       instructions="Bạn là trợ lý tiếng Việt, trả lời ngắn gọn.",   # ~ vai trò 'system'
    #   )
    #   print(r.output_text)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
