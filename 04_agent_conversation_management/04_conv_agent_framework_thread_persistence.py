"""
====================================================================
LAB 04/04 · Agent Framework: lưu/khôi phục trạng thái hội thoại
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework (AgentSession + FileHistoryProvider) + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: ChatHistory của Semantic Kernel -> Agent Framework.
Chạy         : uv run 04_agent_conversation_management/04_conv_agent_framework_thread_persistence.py
Trọng tâm    : DÙNG ĐÚNG cơ chế framework — AgentSession (định danh phiên) + FileHistoryProvider
               (tự lưu/nạp message ra file theo session_id). KHÔNG tự ghép JSON rồi NHỒI lịch sử
               vào prompt như bản cũ. Credential tạo 1 lần, dọn qua 'with'.
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

# ── xác thực ────────────────────────────────────────────────────
from azure.identity import DefaultAzureCredential

# ── SDK Agent Framework ─────────────────────────────────────────
# AgentSession: định danh phiên. FileHistoryProvider: context provider tự lưu/nạp lịch sử ra file.
from agent_framework import Agent, AgentSession, FileHistoryProvider
from agent_framework.foundry import FoundryChatClient

HISTORY_DIR = os.path.join("assets", "output", "agent_history")   # nơi lưu lịch sử hội thoại
SESSION_ID = "user-dai"                                            # 1 phiên = 1 người dùng / 1 cuộc


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
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")
    os.makedirs(HISTORY_DIR, exist_ok=True)

    with DefaultAzureCredential() as credential:
        chat_client = FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=credential,
        )
        # Gắn FileHistoryProvider -> agent TỰ lưu message ra file theo session_id (load_messages=True).
        agent = Agent(
            client=chat_client,
            name="ai103-persist-agent",
            instructions="Bạn là trợ lý tiếng Việt, nhớ ngữ cảnh đã trao đổi.",
            context_providers=[FileHistoryProvider(HISTORY_DIR)],
        )

        # ── Phiên 1: hỏi — framework TỰ lưu lịch sử (không cần serialize tay) ──
        session = AgentSession(session_id=SESSION_ID)
        first = await agent.run("Tên tôi là Đại.", session=session)
        print("Phiên 1:", first.text)

        # ── Phiên 2 (giả lập restart): cùng session_id -> lịch sử TỰ được nạp lại ──
        # Không gửi lại lịch sử, không nhồi vào prompt — provider lo việc đó.
        restored_session = AgentSession(session_id=SESSION_ID)
        second = await agent.run("Tên tôi là gì?", session=restored_session)
        print("Phiên 2:", second.text)

        # ── Đối chiếu · bản GHÉP TAY (bản cũ — serialize JSON rồi NHỒI prompt) ──
        # Nhược điểm: tự quản history, tốn token vì dồn cả lịch sử vào mỗi prompt, dễ sai định dạng.
        #   history += [{"role": "user", "content": q1}, {"role": "assistant", "content": r1.text}]
        #   json.dump(history, open(STATE_FILE, "w"))
        #   context_str = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        #   r2 = await agent.run(f"Dựa trên hội thoại:\n{context_str}\nHỏi: Tên tôi là gì?")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
