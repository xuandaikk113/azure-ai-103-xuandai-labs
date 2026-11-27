"""
====================================================================
LAB 02/02 · Responses API (chuẩn mới agentic / multi-turn)
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI (Responses API)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT (v1: bỏ api_version)
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
from openai import OpenAI   # client trỏ endpoint Azure OpenAI /v1 (cách khuyến nghị)


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
        "AZURE_OPENAI_CHAT_DEPLOYMENT",
    )

    # Cách KHUYẾN NGHỊ (v1): base_url trỏ /openai/v1/, KHÔNG cần api_version.
    client = OpenAI(
        base_url=cfg["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1/",
        api_key=cfg["AZURE_OPENAI_API_KEY"],
    )
    # Alternative CLASSIC (vẫn hỗ trợ, chưa deprecated) - xem file 02/01:
    #   from openai import AzureOpenAI
    #   client = AzureOpenAI(azure_endpoint=cfg["AZURE_OPENAI_ENDPOINT"],
    #                        api_key=cfg["AZURE_OPENAI_API_KEY"], api_version="2025-04-01-preview")
    # Alternative KEYLESS (Entra ID, khuyến nghị production) — thay cho api_key:
    #   from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    #   token_provider = get_bearer_token_provider(
    #       DefaultAzureCredential(), "https://ai.azure.com/.default")   # scope cho /openai/v1
    #   client = OpenAI(base_url=..., api_key=token_provider)

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

    # ── Alternative · cùng tác vụ bằng CHAT COMPLETIONS (cổ điển, xem lab 02/01) ──
    #   r = client.chat.completions.create(
    #       model=cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"],
    #       messages=[{"role": "system", "content": "Bạn là trợ lý tiếng Việt, trả lời ngắn gọn."},
    #                 {"role": "user", "content": "Responses API khác Chat Completions ở điểm nào?"}],
    #   )
    #   print(r.choices[0].message.content)
    # Khác chính: responses dùng 'input'/'instructions' + output_text + previous_response_id (state nhẹ).


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
