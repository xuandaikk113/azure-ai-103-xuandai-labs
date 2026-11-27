"""
====================================================================
LAB 04/05 · Bộ nhớ dài hạn + nén ngữ cảnh (context compaction)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework (FileMemoryProvider + ContextWindowCompactionStrategy)
               trên Azure OpenAI (OpenAIChatClient /v1)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT (v1: bỏ api_version)
SDK tiền nhiệm: tự quản memory + tự tóm tắt bằng tay -> provider/strategy dựng sẵn của Agent Framework.
Chạy         : uv run 04_agent_conversation_management/05_conv_memory_store_and_context_compaction.py
Trọng tâm    : DÙNG ĐÚNG cơ chế framework:
               - Bộ nhớ dài hạn: FileMemoryProvider (tự trích/ghi nhớ fact người dùng, tự recall).
                 Foundry-managed tương đương: agent_framework.foundry.FoundryMemoryProvider.
               - Nén ngữ cảnh: ContextWindowCompactionStrategy (tự nén khi hội thoại dài), gắn vào Agent.
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import asyncio

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── SDK Agent Framework ─────────────────────────────────────────
from agent_framework import (
    Agent, AgentSession,
    FileMemoryProvider, FileSystemAgentFileStore,   # bộ nhớ dài hạn lưu ra file
    ContextWindowCompactionStrategy,                 # nén ngữ cảnh dựng sẵn
)
from agent_framework.openai import OpenAIChatClient   # client Agent Framework trỏ Azure OpenAI /v1

MEMORY_DIR = os.path.join("assets", "output", "agent_memory")   # nơi lưu memory
SESSION_ID = "user-dai"


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


async def main() -> None:
    cfg = require_env(
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_CHAT_DEPLOYMENT",
    )
    os.makedirs(MEMORY_DIR, exist_ok=True)

    chat_client = OpenAIChatClient(
        model=cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"],
        base_url=cfg["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1/",
        api_key=cfg["AZURE_OPENAI_API_KEY"],          # optional — bỏ nếu keyless (token provider)
    )

    # Bộ nhớ dài hạn: provider tự trích fact từ hội thoại và recall ở phiên sau.
    memory = FileMemoryProvider(store=FileSystemAgentFileStore(MEMORY_DIR), source_id="user_memory")
    # Nén ngữ cảnh: khi hội thoại vượt ngưỡng cửa sổ, framework tự nén (không cần tóm tắt tay).
    compaction = ContextWindowCompactionStrategy(max_context_window_tokens=8000, max_output_tokens=1000)

    agent = Agent(
        client=chat_client,
        name="ai103-memory-agent",
        instructions="Bạn là trợ lý tiếng Việt, ghi nhớ sở thích người dùng để cá nhân hoá.",
        context_providers=[memory],
        compaction_strategy=compaction,
    )

    # 1) Người dùng nêu sở thích -> memory TỰ ghi nhớ (không cần save_memory tay).
    session = AgentSession(session_id=SESSION_ID)
    first = await agent.run("Tôi thích uống trà sen.", session=session)
    print("Phiên 1:", first.text)

    # 2) Phiên sau -> memory TỰ recall sở thích để gợi ý cá nhân hoá.
    later = await agent.run("Gợi ý cho tôi 1 món đồ uống.", session=AgentSession(session_id=SESSION_ID))
    print("Gợi ý cá nhân hoá:", later.text)
    # Context compaction đã bật ở trên: hội thoại dài sẽ tự được nén, giữ ý chính, giảm token.

    # ── Đối chiếu · bản GHÉP TAY (bản cũ — tự lưu JSON + tự gọi model tóm tắt) ──
    #   facts = load_memory(); facts.append("..."); save_memory(facts)
    #   client.chat.completions.create(messages=[{"role":"system","content":"Ghi nhớ:\n"+...}])
    #   summary = (tóm tắt thủ công bằng 1 lời gọi model)
    # Nhược điểm: tự quản vòng đời memory + tự chọn lúc nén; framework lo sẵn qua provider/strategy.


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
