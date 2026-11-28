"""
====================================================================
LAB 05/05 · Group chat / Reflection loop: Generator <-> Critic
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework (GroupChatBuilder) + Foundry
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: AutoGen + Semantic Kernel -> Agent Framework.
Chạy         : uv run 05_multi_agent_orchestration_patterns/05_orch_group_chat_reflection_loop.py
Trọng tâm    : GroupChatBuilder điều phối LƯỢT NÓI chung giữa nhiều agent
               (transcript chung), có max_rounds làm chặn an toàn và dừng sớm
               ngay khi phát hiện MARKER chặt ('PASS') — tránh so khớp lỏng
               'ĐẠT' (dễ khớp nhầm khi model nói 'CHƯA ĐẠT').
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

# Marker chuẩn để critic báo ĐẠT — bắt buộc nằm ở đầu câu trả lời nếu slogan đạt yêu cầu
PASS_MARKER = "PASS"


def require_env(*names: str) -> dict:
    """Nạp .env và kiểm tra các biến cấu hình bắt buộc; dừng sớm nếu thiếu biến nào."""
    load_dotenv()  # Đọc file .env nếu có ở thư mục hiện tại/cha
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)  # Lấy giá trị biến môi trường theo tên
        if value:
            values[name] = value  # Lưu vào dict kết quả nếu đã có giá trị
        else:
            missing.append(name)  # Ghi nhận tên biến còn thiếu
    if missing:
        # Thoát chương trình và báo rõ biến nào cần thêm vào .env
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def make_agent(chat_client: FoundryChatClient, name: str, instructions: str) -> Agent:
    """Tạo agent dùng CHUNG chat_client để tránh khởi tạo lặp lại credential/client."""
    return Agent(client=chat_client, name=name, instructions=instructions)


def is_approved(feedback: str) -> bool:
    """Trả về True nếu phản hồi bắt đầu bằng PASS_MARKER chặt (sau khi chuẩn hóa khoảng trắng/chữ hoa).

    Không dùng toán tử 'in' với từ 'ĐẠT' vì chuỗi như 'CHƯA ĐẠT' cũng chứa 'ĐẠT'
    dẫn đến dừng vòng lặp sai thời điểm.
    """
    if not feedback:
        return False
    return feedback.strip().upper().startswith(PASS_MARKER)


def _extract_last_speaker_and_text(messages: object) -> tuple[str, str]:
    """Trích xuất (tên người nói cuối, nội dung text cuối) một cách an toàn từ lịch sử hội thoại.

    Hỗ trợ linh hoạt khi with_termination_condition nhận list/sequence message hoặc object trạng thái.
    """
    # Nếu là object có thuộc tính messages/history thì lấy danh sách message bên trong
    if not isinstance(messages, (list, tuple)):
        for attr in ("messages", "history", "conversation"):
            candidate = getattr(messages, attr, None)
            if isinstance(candidate, (list, tuple)):
                messages = candidate
                break

    if not isinstance(messages, (list, tuple)) or not messages:
        return "", ""

    last_msg = messages[-1]  # Lấy message mới nhất trong transcript chung

    # Lấy tên tác giả/người gửi nếu có
    author = (
        getattr(last_msg, "author_name", None)
        or getattr(last_msg, "name", None)
        or getattr(last_msg, "role", None)
        or ""
    )
    if isinstance(last_msg, dict):
        author = last_msg.get("author_name") or last_msg.get("name") or last_msg.get("role") or ""
        text = last_msg.get("text") or last_msg.get("content") or ""
    else:
        # Ưu tiên thuộc tính .text; nếu không có thì thử .content
        text = getattr(last_msg, "text", None)
        if text is None:
            text = getattr(last_msg, "content", "")

    # Nếu content là danh sách các block/part (ví dụ text block), ghép chuỗi text lại
    if isinstance(text, list):
        parts = []
        for part in text:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(str(part.get("text", "")))
            else:
                parts.append(str(getattr(part, "text", "")))
        text = "".join(parts)

    return str(author).lower(), str(text)


def should_terminate_on_pass(state_or_messages: object) -> bool:
    """Điều kiện dừng sớm: dừng ngay khi 'critic' trả lời duyệt bằng PASS_MARKER."""
    author, text = _extract_last_speaker_and_text(state_or_messages)
    # Chỉ coi là duyệt khi người nói là critic (nếu có thông tin author) và bắt đầu bằng PASS
    if author and "critic" not in author:
        return False
    return is_approved(text)


async def main() -> None:
    # 1. Đọc và xác thực biến môi trường cần thiết cho Foundry
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")

    # 2. Mở context manager cho DefaultAzureCredential để quản lý vòng đời token sạch sẽ
    with DefaultAzureCredential() as credential:
        # 3. Khởi tạo 1 FoundryChatClient dùng chung cho mọi agent trong workflow
        chat_client = FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=credential,
        )

        # 4. Tạo hai agent: generator viết/sửa slogan, critic chấm và đưa phản hồi theo format chặt
        generator = make_agent(
            chat_client,
            name="generator",
            instructions=(
                "Bạn là copywriter. Viết hoặc chỉnh sửa slogan ngắn gọn, giàu cảm xúc "
                "dựa trên góp ý mới nhất của critic. Chỉ đưa ra phương án slogan rõ ràng."
            ),
        )
        critic = make_agent(
            chat_client,
            name="critic",
            instructions=(
                "Bạn là giám khảo đánh giá slogan. Kiểm tra độ ngắn gọn, gợi hình và đúng chủ đề. "
                f"Nếu slogan đã đạt: chỉ trả lời đúng '{PASS_MARKER}' ở đầu. "
                "Nếu chưa đạt: trả lời đúng định dạng 'REVISE: <1 điểm cần sửa cụ thể nhất>'."
            ),
        )

        # 5. Bài toán đầu vào cho nhóm thảo luận
        task = "Slogan cho quán cà phê sách yên tĩnh."

        # 6. Xây dựng GroupChat workflow:
        # - participants: các agent chia sẻ chung transcript và luân phiên phát biểu
        # - with_termination_condition: dừng sớm ngay khi critic duyệt ('PASS')
        # - with_max_rounds: giới hạn trên (6 lượt) để đảm bảo luôn dừng dù chưa đạt PASS
        workflow = (
            GroupChatBuilder(participants=[generator, critic])
            .with_termination_condition(should_terminate_on_pass)
            .with_max_rounds(6)
            .build()
        )

        # 7. Thực thi workflow bất đồng bộ và in toàn bộ output/transcript thu được
        result = await workflow.run(task)
        print("== Transcript group chat ==")
        for output in result.get_outputs():
            print(output)


if __name__ == "__main__":
    # Điểm vào chuẩn của file script độc lập; bắt lỗi cấp cao nhất và thoát gọn
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")