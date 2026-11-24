"""
====================================================================
LAB 04/01 · Hội thoại stateless: tự quản mảng messages + tự cắt lịch sử
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT
SDK tiền nhiệm: cách cơ bản nhất, chưa dùng state phía server.
Chạy         : uv run 04_agent_conversation_management/01_conv_stateless_manual_message_history.py
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


def trim_history(messages: list, max_turns: int = 6) -> list:
    """Giữ system message + max_turns lượt gần nhất (tránh vượt context window)."""
    system_msgs = [m for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    return system_msgs + rest[-max_turns:]


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
    deployment = cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    # CLIENT tự giữ toàn bộ lịch sử trong biến messages (stateless phía server)
    messages = [{"role": "system", "content": "Bạn là trợ lý tiếng Việt."}]
    for question in ["Thủ đô Pháp là gì?", "Dân số ở đó khoảng bao nhiêu?"]:
        messages.append({"role": "user", "content": question})
        messages = trim_history(messages)                # cắt bớt nếu dài
        r = client.chat.completions.create(model=deployment, messages=messages)
        reply = r.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(f"User: {question}\nBot : {reply}\n")

    print("Lưu ý: stateless -> client phải GỬI LẠI toàn bộ lịch sử mỗi lượt (tốn token khi dài).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
