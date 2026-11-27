"""
====================================================================
LAB 05/02 · Orchestration song song (Concurrent): fan-out -> fan-in
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework (ConcurrentBuilder) + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/02_orch_concurrent_fan_out_fan_in.py
Trọng tâm    : ConcurrentBuilder chạy nhiều agent SONG SONG (fan-out) rồi gom (fan-in) qua aggregator.
               Aggregator GẮN NHÃN nguồn (executor_id) để bước tổng hợp không lẫn góc nhìn.
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
from agent_framework import Agent, AgentExecutorResponse
from agent_framework.foundry import FoundryChatClient
# ConcurrentBuilder: fan-out/fan-in DỰNG SẴN (gói agent-framework-orchestrations).
from agent_framework.orchestrations import ConcurrentBuilder


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


def labeled_aggregator(responses: list[AgentExecutorResponse]) -> str:
    """Fan-in: gộp kết quả các nhánh, GẮN NHÃN theo executor_id (tên agent nguồn).

    Có nhãn -> bước/đọc tổng hợp không nhầm góc nhìn (marketing vs technical vs risk).
    """
    return "\n\n".join(
        f"== {response.executor_id} ==\n{response.agent_response.text}"
        for response in responses
    )


async def main() -> None:
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")
    product = "Một app học tiếng Anh bằng AI"

    with DefaultAzureCredential() as credential:
        chat_client = FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=credential,
        )

        # 3 chuyên gia phân tích ở các góc nhìn khác nhau.
        marketing = make_agent(chat_client, "marketing", "Phân tích góc MARKETING, cho 2 ý.")
        technical = make_agent(chat_client, "technical", "Phân tích góc KỸ THUẬT, cho 2 ý.")
        risk = make_agent(chat_client, "risk", "Phân tích RỦI RO, cho 2 ý.")

        # ── API THẬT · ConcurrentBuilder (fan-out song song + fan-in có nhãn) ──
        workflow = (
            ConcurrentBuilder(participants=[marketing, technical, risk])
            .with_aggregator(labeled_aggregator)
            .build()
        )
        result = await workflow.run(f"Sản phẩm: {product}")
        print("== Tổng hợp (có nhãn nguồn) ==")
        for output in result.get_outputs():
            print(output)

        # ── Đối chiếu · bản GHÉP TAY bằng asyncio.gather (bản cũ) ──
        # Lưu ý an toàn: dùng return_exceptions=True để 1 nhánh lỗi KHÔNG làm hỏng cả mẻ;
        # và nhớ GẮN NHÃN khi ghép (bản cũ join trần -> mất nguồn, dễ lẫn góc nhìn).
        #   agents = {"marketing": marketing, "technical": technical, "risk": risk}
        #   results = await asyncio.gather(
        #       *(a.run(f"{product}: cho 2 ý.") for a in agents.values()),
        #       return_exceptions=True,
        #   )
        #   labeled = "\n".join(
        #       f"== {name} ==\n{r.text}" for name, r in zip(agents, results)
        #       if not isinstance(r, Exception)
        #   )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
