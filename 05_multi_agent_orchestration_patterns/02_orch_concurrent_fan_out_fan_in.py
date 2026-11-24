"""
====================================================================
LAB 05/02 · Orchestration song song (Concurrent): fan-out -> fan-in
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/02_orch_concurrent_fan_out_fan_in.py
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import asyncio                  # asyncio.gather để chạy nhiều agent SONG SONG

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
    product = "Một app học tiếng Anh bằng AI"

    # FAN-OUT: 3 chuyên gia phân tích SONG SONG ở các góc nhìn khác nhau
    perspectives = {
        "marketing": "Phân tích góc marketing.",
        "technical": "Phân tích góc kỹ thuật.",
        "risk": "Phân tích rủi ro.",
    }
    agents = {name: make_agent(cfg, name, instr) for name, instr in perspectives.items()}

    # gather chạy đồng thời -> nhanh hơn chạy lần lượt
    results = await asyncio.gather(
        *(agent.run(f"{product}: cho 2 ý.") for agent in agents.values())
    )
    for name, result in zip(agents.keys(), results):
        print(f"== {name} ==\n{result.text}\n")

    # FAN-IN: 1 agent tổng hợp mọi kết quả thành kết luận
    aggregator = make_agent(cfg, "aggregator", "Tổng hợp các phân tích thành kết luận ngắn.")
    summary = await aggregator.run(
        "Tổng hợp các phân tích sau:\n" + "\n".join(r.text for r in results)
    )
    print("== Tổng hợp ==\n", summary.text)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
