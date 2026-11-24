"""
====================================================================
LAB 02/02 · Responses API (chuẩn mới agentic / multi-turn)
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI (Responses API)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT
SDK tiền nhiệm: Chat Completions API + Assistants API -> hợp nhất về Responses API.
Chạy         : uv run 02_genai_chat_alternatives/02_chat_openai_sdk_responses_api.py
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
from openai import AzureOpenAI


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

    # responses.create: thay cho chat.completions. Tham số 'input' nhận chuỗi hoặc danh sách item.
    resp = client.responses.create(
        model=cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"],
        instructions="Bạn là trợ lý tiếng Việt, trả lời ngắn gọn.",   # ~ system message
        input="Responses API khác Chat Completions ở điểm nào?",
    )

    # output_text: thuộc tính tiện lấy toàn bộ text trả về (gộp các output item)
    print("Trả lời:", resp.output_text)
    # resp.id dùng để nối lượt sau qua previous_response_id (xem lab 04/03)
    print("response id:", resp.id)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
