"""
====================================================================
LAB 05/01 · Orchestration tuần tự (Sequential): Researcher -> Writer -> Reviewer
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework (orchestration dựng sẵn) + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/01_orch_sequential_pipeline_workflow.py
Trọng tâm    : DÙNG ĐÚNG SequentialBuilder (gói agent-framework-orchestrations) — builder tự nối
               output bước trước thành input bước sau, KHÔNG ghép await thủ công.
               Credential + chat_client tạo MỘT LẦN, dùng chung cho mọi agent. API async, Python >= 3.11.
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
# SequentialBuilder: orchestration tuần tự DỰNG SẴN (gói agent-framework-orchestrations).
from agent_framework.orchestrations import SequentialBuilder


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

    # Tạo credential + chat_client MỘT LẦN; credential đóng gọn qua 'with' (dọn tài nguyên).
    with DefaultAzureCredential() as credential:
        chat_client = FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=credential,
        )

        researcher = make_agent(chat_client, "researcher", "Nêu 3 ý chính ngắn gọn về chủ đề được hỏi.")
        writer = make_agent(chat_client, "writer", "Viết 1 đoạn văn mạch lạc từ các ý được cho.")
        reviewer = make_agent(chat_client, "reviewer", "Góp ý ngắn gọn để cải thiện đoạn văn.")

        topic = "Lợi ích của RAG trong ứng dụng AI"

        # ── API THẬT · SequentialBuilder ──────────────────────────────
        # participants theo thứ tự: researcher -> writer -> reviewer.
        # Builder tự chuyển output của executor trước thành input của executor sau.
        workflow = SequentialBuilder(participants=[researcher, writer, reviewer]).build()
        result = await workflow.run(f"Chủ đề: {topic}")
        # get_outputs(): danh sách output cuối của workflow (hội thoại/các message kết).
        print("== Kết quả workflow (sequential) ==")
        for output in result.get_outputs():
            print(output)

        # ── Đối chiếu · bản GHÉP TAY (bản cũ — chỉ để hiểu luồng, không khuyến nghị) ──
        #   research = await researcher.run(f"Nêu 3 ý về: {topic}")
        #   draft = await writer.run(f"Viết đoạn từ các ý:\n{research.text}")
        #   review = await reviewer.run(f"Góp ý cho đoạn:\n{draft.text}")
        # Nhược điểm bản tay: tự truyền .text từng chặng, không có checkpoint/trace của workflow.


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
