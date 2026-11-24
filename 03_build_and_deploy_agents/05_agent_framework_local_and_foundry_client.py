"""
====================================================================
LAB 03/05 · Microsoft Agent Framework: FoundryChatClient (+ client khác)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework (code-first) + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: Semantic Kernel + AutoGen -> HỢP NHẤT thành Microsoft Agent Framework.
Chạy         : uv run 03_build_and_deploy_agents/05_agent_framework_local_and_foundry_client.py
Lưu ý        : Agent Framework là ASYNC-first (dùng asyncio) và cần Python >= 3.11.
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import asyncio                  # Agent Framework chạy bất đồng bộ

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── xác thực ────────────────────────────────────────────────────
from azure.identity import DefaultAzureCredential

# ── SDK Agent Framework ─────────────────────────────────────────
# agent_framework: class Agent (lớp agent code-first, KHÔNG phải ChatAgent).
from agent_framework import Agent
# agent_framework.foundry: FoundryChatClient (gói agent-framework-foundry) -> dùng endpoint Responses của Foundry.
from agent_framework.foundry import FoundryChatClient
# Client khác (cùng một API Agent): from agent_framework.openai import OpenAIChatClient


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

    # Tạo agent bằng FoundryChatClient (xác thực keyless qua credential)
    agent = Agent(
        client=FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=DefaultAzureCredential(),
        ),
        name="ai103-af-agent",
        instructions="Bạn là trợ lý tiếng Việt, trả lời ngắn gọn.",
    )

    # run() là coroutine -> await. result.text là câu trả lời.
    result = await agent.run("Microsoft Agent Framework hợp nhất những gì?")
    print("Trả lời:", result.text)

    # Đổi provider mà KHÔNG đổi code agent: chỉ thay client=OpenAIChatClient()
    # -> cùng một API Agent chạy được nhiều nhà cung cấp (local/OpenAI/Foundry).


if __name__ == "__main__":
    try:
        asyncio.run(main())     # chạy coroutine main() trong event loop
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
