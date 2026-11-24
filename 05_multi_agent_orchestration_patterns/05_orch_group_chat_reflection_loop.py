"""
====================================================================
LAB 05/05 · Group chat / Reflection loop: Generator <-> Critic
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/05_orch_group_chat_reflection_loop.py
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

    generator = make_agent(cfg, "generator", "Viết slogan ngắn cho sản phẩm.")
    critic = make_agent(cfg, "critic",
                        "Chấm slogan. Nếu hay thì trả đúng 'ĐẠT'. Nếu chưa, nêu 1 điểm cần sửa.")

    task = "Slogan cho quán cà phê sách yên tĩnh."
    draft = (await generator.run(task)).text
    print("Bản nháp đầu:", draft)

    # Vòng lặp phản biện: lặp tối đa 3 lần hoặc tới khi critic nói ĐẠT
    for round_num in range(1, 4):
        feedback = (await critic.run(f"Chấm slogan: {draft}")).text
        print(f"\n[Vòng {round_num}] Critic: {feedback}")
        if "ĐẠT" in feedback.upper():
            break
        # Generator sửa theo góp ý (self-critique nâng chất lượng)
        draft = (await generator.run(
            f"Sửa slogan theo góp ý: {feedback}\nSlogan cũ: {draft}"
        )).text
        print(f"[Vòng {round_num}] Sửa: {draft}")

    print("\nSlogan cuối:", draft)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
