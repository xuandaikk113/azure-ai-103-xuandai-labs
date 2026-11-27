"""
====================================================================
LAB 04/03 · Nối hội thoại bằng previous_response_id (Responses API)
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI (Responses API)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT (v1: bỏ api_version)
SDK tiền nhiệm: không.
Chạy         : uv run 04_agent_conversation_management/03_conv_responses_api_previous_response_id.py
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
    deployment = cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    # Lượt 1: lấy response id
    first_response = client.responses.create(model=deployment, input="Thủ đô nước Pháp là gì?")
    print("Lượt 1:", first_response.output_text)

    # Lượt 2: KHÔNG gửi lại lịch sử, chỉ nối qua previous_response_id
    # -> server tự dùng ngữ cảnh của lượt trước (state nhẹ phía server).
    second_response = client.responses.create(
        model=deployment,
        input="Dân số ở đó khoảng bao nhiêu?",
        previous_response_id=first_response.id,   # optional — bỏ đi thì model KHÔNG nhớ lượt trước
    )
    print("Lượt 2:", second_response.output_text)

    print("\nƯu điểm: không phải gửi lại toàn bộ lịch sử như stateless (04/01).")

    # ── Alternative · chat.completions KHÔNG có previous_response_id ──
    # Muốn nhớ ngữ cảnh với chat.completions thì PHẢI tự gửi lại toàn bộ 'messages' (xem 04/01),
    # hoặc để server giữ state bằng Conversations API (xem 04/02).


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
