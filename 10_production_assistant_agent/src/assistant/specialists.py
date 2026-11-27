"""Các specialist agent — mỗi intent 1 agent, gắn đúng tool cần dùng.

Dùng chung 1 chat_client (1 model) nhưng instructions + tools khác nhau. Router sẽ handoff
tin nhắn tới agent phù hợp.
"""

from agent_framework import Agent

from .tools import book_meeting, log_work, search_internal_docs, search_web, analyze_sales

# Danh sách intent hợp lệ (dùng chung với router để validate nhãn triage trả về).
SPECIALIST_INTENTS: tuple[str, ...] = (
    "qa", "chitchat", "meetings", "docs", "worklog", "web", "sales",
)


def build_specialists(chat_client) -> dict[str, Agent]:
    """Dựng toàn bộ specialist agent, trả map intent -> Agent."""

    def make(name: str, instructions: str, tools: list | None = None) -> Agent:
        return Agent(client=chat_client, name=name, instructions=instructions, tools=tools or [])

    return {
        "qa": make(
            "qa",
            "Trả lời câu hỏi kiến thức chung, ngắn gọn và chính xác. Nếu không chắc, hãy nói không chắc.",
        ),
        "chitchat": make(
            "chitchat",
            "Tán gẫu thân thiện, tự nhiên, ngắn gọn bằng tiếng Việt.",
        ),
        "meetings": make(
            "meetings",
            "Giúp người dùng ĐẶT PHÒNG HỌP. Trích đủ title/date/start_time từ yêu cầu rồi gọi tool "
            "book_meeting. Nếu thiếu thông tin bắt buộc thì hỏi lại trước khi đặt.",
            [book_meeting],
        ),
        "docs": make(
            "docs",
            "Tra cứu TÀI LIỆU NỘI BỘ bằng tool search_internal_docs, rồi tóm tắt câu trả lời kèm tên tài liệu nguồn.",
            [search_internal_docs],
        ),
        "worklog": make(
            "worklog",
            "Giúp người dùng GHI NHẬN CÔNG VIỆC. Trích task + số giờ rồi gọi tool log_work.",
            [log_work],
        ),
        "web": make(
            "web",
            "Tìm thông tin MỚI trên internet bằng tool search_web, rồi trả lời kèm nguồn.",
            [search_web],
        ),
        "sales": make(
            "sales",
            "Phân tích DỮ LIỆU BÁN HÀNG bằng tool analyze_sales (text2sql + biểu đồ). Diễn giải kết quả ngắn gọn.",
            [analyze_sales],
        ),
    }
