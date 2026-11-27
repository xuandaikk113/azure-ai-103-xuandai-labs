"""
====================================================================
LAB 05/04 · Supervisor gọi agent con như TOOL (agent-as-tool)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework (.as_tool / MagenticBuilder) + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/04_orch_supervisor_as_tool_pattern.py
Trọng tâm    : DÙNG ĐÚNG agent.as_tool() — supervisor có các agent con làm TOOL và TỰ QUYẾT gọi tool
               nào (kiểm soát tập trung), KHÔNG gọi cứng tuần tự như bản cũ.
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
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def make_agent(chat_client, name: str, instructions: str) -> Agent:
    """Tạo agent dùng CHUNG chat_client (không tạo lại credential/client mỗi agent)."""
    return Agent(client=chat_client, name=name, instructions=instructions)


async def main() -> None:
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")

    with DefaultAzureCredential() as credential:
        chat_client = FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=credential,
        )

        # Agent con chuyên biệt.
        translator = make_agent(chat_client, "translator", "Dịch câu sang tiếng Anh. Chỉ trả bản dịch.")
        summarizer = make_agent(chat_client, "summarizer", "Tóm tắt 1 câu. Chỉ trả tóm tắt.")

        # ── API THẬT · agent.as_tool() ────────────────────────────────
        # Biến agent con thành TOOL -> supervisor tự quyết gọi tool nào, khi nào.
        translate_tool = translator.as_tool(
            name="translate", description="Dịch văn bản sang tiếng Anh", arg_name="text",
        )
        summarize_tool = summarizer.as_tool(
            name="summarize", description="Tóm tắt văn bản trong 1 câu", arg_name="text",
        )
        supervisor = Agent(
            client=chat_client,
            name="supervisor",
            instructions="Bạn điều phối: dùng tool translate và summarize khi cần, rồi tổng hợp kết quả cho người dùng.",
            tools=[translate_tool, summarize_tool],
        )

        text = "Trí tuệ nhân tạo đang thay đổi cách con người làm việc mỗi ngày."
        result = await supervisor.run(f"Hãy dịch sang tiếng Anh và tóm tắt câu sau: {text}")
        print("Supervisor:", result.text)

        # ── Mở rộng · MagenticBuilder (manager điều phối nhiều agent có kế hoạch) ──
        # Khi cần "manager" lập kế hoạch + điều phối phức tạp hơn as_tool:
        #   from agent_framework.orchestrations import MagenticBuilder
        #   workflow = MagenticBuilder(participants=[translator, summarizer],
        #                              manager_agent=supervisor, max_round_count=5).build()
        #   result = await workflow.run(text)

        # ── Đối chiếu · bản GHÉP TAY (gọi cứng tuần tự — bản cũ, KHÔNG phải as_tool) ──
        #   translation = (await translator.run(text)).text
        #   summary = (await summarizer.run(text)).text
        #   result = await supervisor.run(f"Tổng hợp: dịch={translation}; tóm tắt={summary}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
