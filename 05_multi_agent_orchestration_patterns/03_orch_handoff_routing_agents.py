"""
====================================================================
LAB 05/03 · Orchestration Handoff: định tuyến tới agent chuyên gia theo intent
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/03_orch_handoff_routing_agents.py
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

    # Router: đọc yêu cầu và quyết định chuyển cho ai (chỉ trả 1 nhãn)
    router = make_agent(cfg, "router",
                        "Phân loại yêu cầu là 'technical' hoặc 'billing'. Chỉ trả đúng 1 từ.")
    specialists = {
        "technical": make_agent(cfg, "tech", "Bạn là CSKH kỹ thuật."),
        "billing": make_agent(cfg, "billing", "Bạn là CSKH thanh toán."),
    }

    request = "Tôi bị trừ tiền 2 lần cho 1 đơn hàng."

    # Bước 1: router phân loại intent
    label = (await router.run(request)).text.strip().lower()
    key = "billing" if "billing" in label else "technical"
    print(f"Router -> handoff cho: {key}")

    # Bước 2: HANDOFF sang agent chuyên gia phù hợp
    reply = await specialists[key].run(request)
    print("Chuyên gia trả lời:", reply.text)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
