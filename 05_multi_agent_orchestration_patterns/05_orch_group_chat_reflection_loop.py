"""
====================================================================
LAB 05/05 · Group chat / Reflection loop: Generator <-> Critic
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework (GroupChatBuilder) + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/05_orch_group_chat_reflection_loop.py
Trọng tâm    : GroupChatBuilder điều phối LƯỢT NÓI chung giữa nhiều agent (transcript chung),
               có max_rounds. Điều kiện dừng dùng MARKER chặt ('PASS') — tránh so khớp 'ĐẠT' lỏng
               (dễ khớp nhầm khi model nói 'CHƯA ĐẠT').
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
# GroupChatBuilder: điều phối group chat DỰNG SẴN (gói agent-framework-orchestrations).
from agent_framework.orchestrations import GroupChatBuilder


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


# Marker chuẩn để báo ĐẠT — critic BUỘC trả đúng token này ở đầu nếu slogan tốt.
PASS_MARKER = "PASS"


def is_approved(feedback: str) -> bool:
    """True nếu critic duyệt. Dùng startswith MARKER chặt, KHÔNG dùng substring 'ĐẠT'
    (vì 'CHƯA ĐẠT' cũng chứa 'ĐẠT' -> dừng sai)."""
    return feedback.strip().upper().startswith(PASS_MARKER)


async def main() -> None:
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")

    with DefaultAzureCredential() as credential:
        chat_client = FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=credential,
        )

        generator = make_agent(chat_client, "generator", "Viết/sửa slogan ngắn cho sản phẩm theo góp ý mới nhất.")
        critic = make_agent(
            chat_client, "critic",
            f"Chấm slogan. Nếu đạt: trả ĐÚNG '{PASS_MARKER}'. Nếu chưa: trả 'REVISE: <1 điểm cần sửa>'.",
        )

        task = "Slogan cho quán cà phê sách yên tĩnh."

        # ── API THẬT · GroupChatBuilder (transcript chung, bounded rounds) ──
        # max_rounds = chặn trên số lượt (an toàn, tránh lặp vô hạn). Orchestrator mặc định
        # luân phiên các participant; có thể tuỳ biến qua orchestrator_agent/selection_func/
        # with_termination_condition nếu muốn dừng theo marker 'PASS'.
        workflow = (
            GroupChatBuilder(participants=[generator, critic])
            .with_max_rounds(6)
            .build()
        )
        result = await workflow.run(task)
        print("== Transcript group chat ==")
        for output in result.get_outputs():
            print(output)

        # ── Đối chiếu · reflection loop GHÉP TAY (ĐÃ SỬA điều kiện dừng #4) ──
        # draft = (await generator.run(task)).text
        # for round_num in range(1, 4):              # max_turns tường minh
        #     feedback = (await critic.run(f"Chấm slogan: {draft}")).text
        #     if is_approved(feedback):              # MARKER chặt, không phải 'ĐẠT' in ...
        #         break
        #     draft = (await generator.run(f"Sửa theo góp ý: {feedback}\nSlogan cũ: {draft}")).text


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
