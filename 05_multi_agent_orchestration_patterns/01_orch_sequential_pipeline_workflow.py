"""
====================================================================
LAB 05/01 · Orchestration tuần tự (Sequential): Researcher -> Writer -> Reviewer
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/01_orch_sequential_pipeline_workflow.py
Ghi chú      : Agent Framework có orchestration dựng sẵn (Sequential/Concurrent/Handoff/Magentic),
               ở đây ghép thủ công bằng await để thấy rõ luồng. API async + Python >= 3.11.
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
    """Tạo 1 agent với client Foundry riêng (an toàn khi chạy song song)."""
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

    researcher = make_agent(cfg, "researcher", "Nêu ý chính ngắn gọn về chủ đề được hỏi.")
    writer = make_agent(cfg, "writer", "Viết 1 đoạn văn mạch lạc từ các ý được cho.")
    reviewer = make_agent(cfg, "reviewer", "Góp ý ngắn gọn để cải thiện đoạn văn.")

    topic = "Lợi ích của RAG trong ứng dụng AI"

    # Tuần tự: output bước trước là input bước sau
    research = await researcher.run(f"Nêu 3 ý chính về: {topic}")
    print("== Researcher ==\n", research.text)

    draft = await writer.run(f"Viết đoạn ngắn dựa trên các ý:\n{research.text}")
    print("\n== Writer ==\n", draft.text)

    review = await reviewer.run(f"Góp ý cho đoạn văn:\n{draft.text}")
    print("\n== Reviewer ==\n", review.text)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
