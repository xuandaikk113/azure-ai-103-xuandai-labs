"""
====================================================================
LAB 05/06 · (NÂNG CAO) WorkflowBuilder: graph Executor + edges (reflection loop có điều kiện)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework (WorkflowBuilder / Executor) + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/06_orch_workflow_builder_graph.py
Trọng tâm    : Khi các builder dựng sẵn (Sequential/Concurrent/Handoff/GroupChat, lab 05/01-05) KHÔNG
               đủ, dùng WorkflowBuilder để tự vẽ GRAPH: Executor (node) nối bằng edge, có VÒNG LẶP
               và ĐIỀU KIỆN dừng. Demo 1: reflection loop Generator<->Critic bằng graph + yield_output.
               Demo 2: GroupChatBuilder + TerminationCondition (callable) dừng theo marker 'PASS'.
Lưu ý        : max_iterations của WorkflowBuilder = chặn trên số bước (an toàn, tránh lặp vô hạn).
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
from agent_framework import Agent, Executor, WorkflowBuilder, WorkflowContext, handler
from agent_framework.foundry import FoundryChatClient
# GroupChatBuilder + TerminationCondition cho demo 2 (dừng theo marker).
from agent_framework.orchestrations import GroupChatBuilder

PASS_MARKER = "PASS"   # critic trả đúng token này ở đầu nếu đạt


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def _text_of(message) -> str:
    """Lấy text an toàn từ 1 message (có thể là ChatMessage/str)."""
    return getattr(message, "text", None) or str(message)


def is_approved(feedback: str) -> bool:
    """Dừng khi critic duyệt — MARKER chặt (startswith 'PASS'), KHÔNG dùng 'ĐẠT' in ... (khớp nhầm)."""
    return feedback.strip().upper().startswith(PASS_MARKER)


# ════════════════════════════════════════════════════════════════
# DEMO 1 · Graph tự vẽ bằng WorkflowBuilder (Executor là node)
# Luồng: [generator] --draft--> [critic] --feedback--> quay lại [generator] (vòng lặp)
#        critic đạt -> yield_output(draft) để KẾT THÚC thay vì gửi tiếp.
# ════════════════════════════════════════════════════════════════
class GeneratorExecutor(Executor):
    """Node sinh/sửa bản nháp theo input (task ban đầu hoặc feedback của critic)."""

    def __init__(self, agent: Agent):
        super().__init__(id="generator")
        self._agent = agent

    @handler
    async def run_step(self, message: str, ctx: WorkflowContext[str]) -> None:
        draft = (await self._agent.run(message)).text
        await ctx.send_message(draft)   # gửi draft sang node tiếp (critic)


class CriticExecutor(Executor):
    """Node chấm bản nháp: đạt -> yield output (kết thúc); chưa -> gửi feedback về generator."""

    def __init__(self, agent: Agent):
        super().__init__(id="critic")
        self._agent = agent

    @handler
    async def run_step(self, draft: str, ctx: WorkflowContext[str, str]) -> None:
        feedback = (await self._agent.run(f"Chấm bản nháp: {draft}")).text
        if is_approved(feedback):
            await ctx.yield_output(draft)   # ĐẠT -> xuất kết quả, dừng nhánh này
        else:
            # Chưa đạt -> gửi feedback kèm bản cũ quay lại generator (tạo VÒNG LẶP).
            await ctx.send_message(f"Sửa theo góp ý: {feedback}\nBản cũ: {draft}")


async def demo_workflow_graph(chat_client) -> None:
    generator = Agent(client=chat_client, name="generator", instructions="Viết/sửa slogan ngắn gọn theo yêu cầu.")
    critic = Agent(
        client=chat_client, name="critic",
        instructions=f"Chấm slogan. Đạt: trả đúng '{PASS_MARKER}'. Chưa: trả 'REVISE: <1 điểm cần sửa>'.",
    )
    generator_node = GeneratorExecutor(generator)
    critic_node = CriticExecutor(critic)

    # start_executor BẮT BUỘC; max_iterations chặn vòng lặp (an toàn).
    workflow = (
        WorkflowBuilder(start_executor=generator_node, max_iterations=10)
        .add_edge(generator_node, critic_node)   # generator -> critic
        .add_edge(critic_node, generator_node)   # critic -> generator (vòng lặp khi chưa đạt)
        .build()
    )
    result = await workflow.run("Slogan cho quán cà phê sách yên tĩnh.")
    print("== DEMO 1 · WorkflowBuilder graph (reflection loop) ==")
    for output in result.get_outputs():   # chứa draft đạt (đã yield_output)
        print(output)


# ════════════════════════════════════════════════════════════════
# DEMO 2 · GroupChatBuilder + TerminationCondition dừng theo 'PASS'
# ════════════════════════════════════════════════════════════════
def stop_when_approved(messages) -> bool:
    """TerminationCondition (callable): dừng group chat khi message cuối bắt đầu bằng 'PASS'."""
    if not messages:
        return False
    return is_approved(_text_of(messages[-1]))


async def demo_group_chat_with_termination(chat_client) -> None:
    generator = Agent(client=chat_client, name="generator", instructions="Viết/sửa slogan ngắn gọn theo góp ý mới nhất.")
    critic = Agent(
        client=chat_client, name="critic",
        instructions=f"Chấm slogan. Đạt: trả đúng '{PASS_MARKER}'. Chưa: trả 'REVISE: <1 điểm>'.",
    )
    # with_termination_condition nhận 1 callable (TerminationCondition là protocol gọi được);
    # with_max_rounds là lưới an toàn thứ hai nếu không bao giờ đạt 'PASS'.
    workflow = (
        GroupChatBuilder(participants=[generator, critic])
        .with_termination_condition(stop_when_approved)
        .with_max_rounds(8)
        .build()
    )
    result = await workflow.run("Slogan cho quán cà phê sách yên tĩnh.")
    print("\n== DEMO 2 · GroupChat + TerminationCondition('PASS') ==")
    for output in result.get_outputs():
        print(output)


async def main() -> None:
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")
    with DefaultAzureCredential() as credential:
        chat_client = FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=credential,
        )
        await demo_workflow_graph(chat_client)
        await demo_group_chat_with_termination(chat_client)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
