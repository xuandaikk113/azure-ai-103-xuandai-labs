"""
====================================================================
LAB 05/04 · Supervisor gọi agent con như TOOL (agent-as-tool)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/04_orch_supervisor_as_tool_pattern.py
Ghi chú      : Agent Framework có .as_tool() để biến agent con thành tool. Ở đây minh hoạ mô hình
               bằng cách supervisor gọi các agent con rồi tổng hợp (kiểm soát tập trung).
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


def make_agent(cfg: dict, name: str, instructions: str) -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=DefaultAzureCredential(),
        ),
        name=name,
        instructions=instructions,
    )


async def main() -> None:
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")

    # Các agent con đóng vai "tool" chuyên biệt
    translate_agent = make_agent(cfg, "translator", "Dịch câu sang tiếng Anh. Chỉ trả bản dịch.")
    summarize_agent = make_agent(cfg, "summarizer", "Tóm tắt 1 câu. Chỉ trả tóm tắt.")

    # Supervisor điều phối: quyết định dùng agent con nào rồi tổng hợp
    supervisor = make_agent(cfg, "supervisor", "Bạn điều phối và tổng hợp kết quả từ trợ lý con.")

    text = "Trí tuệ nhân tạo đang thay đổi cách con người làm việc mỗi ngày."

    # Supervisor "gọi tool" = gọi agent con (ở đây minh hoạ trực tiếp)
    translation = (await translate_agent.run(text)).text
    summary = (await summarize_agent.run(text)).text

    result = await supervisor.run(
        f"Tổng hợp cho người dùng:\n- Bản dịch: {translation}\n- Tóm tắt: {summary}"
    )
    print("Supervisor:", result.text)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
