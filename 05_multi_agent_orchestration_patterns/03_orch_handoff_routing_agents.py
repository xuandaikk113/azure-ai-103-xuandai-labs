"""
====================================================================
LAB 05/03 · Orchestration Handoff: định tuyến tới agent chuyên gia theo intent
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework (HandoffBuilder) + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/03_orch_handoff_routing_agents.py
Trọng tâm    : HandoffBuilder tạo cơ chế HANDOFF THẬT (agent bắt đầu tự "chuyển giao" cho agent đích
               qua tool do framework sinh), KHÔNG phải tự so khớp chuỗi label bằng tay.
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
# HandoffBuilder: orchestration handoff DỰNG SẴN (gói agent-framework-orchestrations).
from agent_framework.orchestrations import HandoffBuilder


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

        triage = make_agent(
            chat_client, "triage",
            "Bạn tiếp nhận yêu cầu khách. Nếu về kỹ thuật thì chuyển cho 'technical', "
            "nếu về thanh toán thì chuyển cho 'billing'.",
        )
        technical = make_agent(chat_client, "technical", "Bạn là CSKH kỹ thuật, trả lời trực tiếp.")
        billing = make_agent(chat_client, "billing", "Bạn là CSKH thanh toán, trả lời trực tiếp.")

        # ── API THẬT · HandoffBuilder ─────────────────────────────────
        # start_agent = triage; triage được phép handoff sang technical/billing.
        # Framework tự sinh "handoff tool" cho triage; triage tự quyết chuyển cho ai.
        workflow = (
            HandoffBuilder(participants=[triage, technical, billing])
            .with_start_agent(triage)
            .add_handoff(triage, [technical, billing])
            .build()
        )
        result = await workflow.run("Tôi bị trừ tiền 2 lần cho 1 đơn hàng.")
        print("== Kết quả (sau handoff) ==")
        for output in result.get_outputs():
            print(output)

        # ── Đối chiếu · bản GHÉP TAY (router trả label + so khớp chuỗi — bản cũ) ──
        # Nhược điểm: 'if "billing" in label' dễ khớp nhầm, không phải handoff thật.
        #   label = (await triage.run(request)).text.strip().lower()
        #   target = billing if "billing" in label else technical
        #   reply = await target.run(request)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
