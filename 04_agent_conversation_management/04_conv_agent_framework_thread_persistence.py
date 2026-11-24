"""
====================================================================
LAB 04/04 · Agent Framework: lưu/khôi phục trạng thái hội thoại
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: ChatHistory của Semantic Kernel -> Agent Framework.
Chạy         : uv run 04_agent_conversation_management/04_conv_agent_framework_thread_persistence.py
Lưu ý        : Agent Framework có AgentSession để quản lý thread server-side; ở đây minh hoạ
               persistence ở mức TRẠNG THÁI (serialize ra JSON) để resume sau — tra sample
               agent-framework cho API AgentSession chính thức.
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import json
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
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient

STATE_FILE = os.path.join("assets", "output", "conv_state.json")


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def build_agent(cfg: dict) -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=DefaultAzureCredential(),
        ),
        name="ai103-persist-agent",
        instructions="Bạn là trợ lý tiếng Việt, nhớ ngữ cảnh đã trao đổi.",
    )


async def main() -> None:
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    agent = build_agent(cfg)

    # ── Phiên 1: hỏi, rồi LƯU trạng thái hội thoại ra JSON ──
    history = []
    q1 = "Tên tôi là Đại."
    r1 = await agent.run(q1)
    history += [{"role": "user", "content": q1}, {"role": "assistant", "content": r1.text}]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False)        # serialize để resume sau
    print("Phiên 1:", r1.text)

    # ── Phiên 2 (giả lập chạy lại): NẠP trạng thái rồi hỏi tiếp dựa trên ngữ cảnh ──
    with open(STATE_FILE, encoding="utf-8") as f:
        history = json.load(f)
    context_str = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    q2 = f"Dựa trên hội thoại trước:\n{context_str}\n\nHỏi: Tên tôi là gì?"
    r2 = await agent.run(q2)
    print("Phiên 2:", r2.text)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
