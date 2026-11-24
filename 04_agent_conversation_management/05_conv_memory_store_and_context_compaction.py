"""
====================================================================
LAB 04/05 · Bộ nhớ dài hạn + nén ngữ cảnh (context compaction)
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT (v1: bỏ api_version)
SDK tiền nhiệm: không.
Chạy         : uv run 04_agent_conversation_management/05_conv_memory_store_and_context_compaction.py
Lưu ý        : Foundry có FoundryMemoryProvider (memory được quản lý). Ở đây minh hoạ thủ công:
               (1) nhớ fact người dùng ra JSON; (2) nén lịch sử dài thành tóm tắt.
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── SDK ─────────────────────────────────────────────────────────
from openai import OpenAI   # client trỏ endpoint Azure OpenAI /v1 (cách khuyến nghị)

MEMORY_FILE = os.path.join("assets", "output", "user_memory.json")


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def save_memory(facts: list) -> None:
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(facts, f, ensure_ascii=False)


def load_memory() -> list:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def compact_context(client, deployment, messages: list) -> str:
    """Nén (tóm tắt) các lượt cũ thành 1 đoạn ngắn để tiết kiệm token."""
    content = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    r = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": f"Tóm tắt hội thoại sau trong 1-2 câu:\n{content}"}],
    )
    return r.choices[0].message.content


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
    deployment = cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    # 1) BỘ NHỚ DÀI HẠN: ghi nhớ fact của người dùng (bền qua nhiều phiên)
    facts = load_memory()
    facts.append("Người dùng thích uống trà sen.")
    save_memory(facts)
    print("Memory hiện có:", facts)

    # 2) Dùng memory để cá nhân hoá câu trả lời
    r = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "Ghi nhớ về người dùng:\n" + "\n".join(facts)},
            {"role": "user", "content": "Gợi ý cho tôi 1 món đồ uống."},
        ],
    )
    print("Gợi ý cá nhân hoá:", r.choices[0].message.content)

    # 3) NÉN NGỮ CẢNH cho hội thoại dài
    long_history = [
        {"role": "user", "content": "Tôi đang lên kế hoạch du lịch Đà Lạt."},
        {"role": "assistant", "content": "Tuyệt! Bạn đi mấy ngày?"},
        {"role": "user", "content": "3 ngày, thích chỗ yên tĩnh."},
    ]
    summary = compact_context(client, deployment, long_history)
    print("Tóm tắt (thay cho lịch sử dài):", summary)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
