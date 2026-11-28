"""
====================================================================
LAB 05/04b · Điều phối đa tác tử có kế hoạch với MagenticBuilder
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework (MagenticBuilder) + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/04b_orch_magentic_builder.py
Trọng tâm    : DÙNG ĐÚNG MagenticBuilder — manager_agent lập kế hoạch và điều phối
               các participants qua nhiều vòng trao đổi, thay vì tự gọi cứng hoặc
               chỉ gọi tool một cấp.
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
from agent_framework.orchestrations import MagenticBuilder


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def make_agent(chat_client: FoundryChatClient, name: str, instructions: str) -> Agent:
    """Tạo agent dùng CHUNG chat_client và credential."""
    return Agent(client=chat_client, name=name, instructions=instructions)


async def main() -> None:
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")

    # Khởi tạo credential và chat_client MỘT LẦN để tái sử dụng cho mọi agent.
    with DefaultAzureCredential() as credential:
        chat_client = FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=credential,
        )

        # Các agent chuyên môn tham gia workflow (participants).
        translator = make_agent(
            chat_client,
            name="translator",
            instructions="Bạn là chuyên gia dịch thuật. Dịch chính xác sang tiếng Anh, giữ sắc thái tự nhiên.",
        )
        summarizer = make_agent(
            chat_client,
            name="summarizer",
            instructions="Bạn là chuyên gia tóm tắt. Tóm tắt ý cốt lõi ngắn gọn trong 1 câu tiếng Việt.",
        )

        # Agent quản lý (manager) lập kế hoạch, chọn participant theo từng bước và chốt kết quả.
        manager = make_agent(
            chat_client,
            name="manager",
            instructions=(
                "Bạn là manager điều phối. Hãy phân công translator dịch sang tiếng Anh "
                "và summarizer tóm tắt 1 câu tiếng Việt, sau đó tổng hợp rõ ràng cho người dùng."
            ),
        )

        # ── API THẬT · MagenticBuilder ────────────────────────────────
        workflow = (
            MagenticBuilder(
                participants=[translator, summarizer],
                manager_agent=manager,
                max_round_count=5,
            )
            .build()
        )

        task = (
            "Xử lý câu sau: 'Trí tuệ nhân tạo đang thay đổi cách con người làm việc mỗi ngày.' "
            "Yêu cầu: có bản dịch tiếng Anh và bản tóm tắt 1 câu tiếng Việt."
        )

        result = await workflow.run(task)

        # Lấy output cuối cùng từ workflow (hỗ trợ cả trường hợp trả về danh sách outputs hoặc .text)
        outputs = result.get_outputs() if hasattr(result, "get_outputs") else []
        if outputs:
            for item in outputs:
                print("Magentic output:", getattr(item, "text", item))
        else:
            print("Magentic result:", getattr(result, "text", result))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")