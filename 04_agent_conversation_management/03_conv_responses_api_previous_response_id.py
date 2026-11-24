"""
====================================================================
LAB 04/03 · Nối hội thoại bằng previous_response_id (Responses API)
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI (Responses API)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT
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
    dep = cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    # Lượt 1: lấy response id
    r1 = client.responses.create(model=dep, input="Thủ đô nước Pháp là gì?")
    print("Lượt 1:", r1.output_text)

    # Lượt 2: KHÔNG gửi lại lịch sử, chỉ nối qua previous_response_id
    # -> server tự dùng ngữ cảnh của lượt trước (state nhẹ phía server).
    r2 = client.responses.create(
        model=dep,
        input="Dân số ở đó khoảng bao nhiêu?",
        previous_response_id=r1.id,
    )
    print("Lượt 2:", r2.output_text)

    print("\nƯu điểm: không phải gửi lại toàn bộ lịch sử như stateless (04/01).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
