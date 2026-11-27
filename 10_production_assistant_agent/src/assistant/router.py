"""Handoff orchestration: triage agent phân loại intent -> chuyển cho specialist tương ứng.

Đây là mẫu handoff tường minh (deterministic, dễ test/giám sát) thay vì để 1 agent tự
quyết mọi thứ — phù hợp production.
"""

from agent_framework import Agent

from .specialists import build_specialists, SPECIALIST_INTENTS

TRIAGE_INSTRUCTIONS = (
    "Bạn là bộ định tuyến. Phân loại tin nhắn người dùng vào ĐÚNG MỘT intent sau và chỉ trả về đúng từ khoá đó:\n"
    "- qa: hỏi đáp kiến thức chung\n"
    "- chitchat: chào hỏi, tán gẫu\n"
    "- meetings: đặt/sửa lịch họp\n"
    "- docs: tra tài liệu/chính sách nội bộ\n"
    "- worklog: ghi nhận giờ làm việc\n"
    "- web: cần thông tin mới trên internet\n"
    "- sales: phân tích số liệu bán hàng\n"
    "Chỉ trả về một từ khoá duy nhất, không thêm gì khác."
)


class AssistantRouter:
    """Điều phối: triage -> handoff sang specialist. Tạo 1 lần, tái dùng cho mọi request."""

    def __init__(self, chat_client):
        self.triage = Agent(client=chat_client, name="triage", instructions=TRIAGE_INSTRUCTIONS)
        self.specialists = build_specialists(chat_client)

    @staticmethod
    def normalize_intent(label: str) -> str:
        """Chuẩn hoá nhãn triage trả về thành 1 intent hợp lệ; không khớp -> 'qa' (fallback an toàn).

        Hàm thuần -> unit test được không cần LLM.
        """
        token = label.strip().lower().split()[0] if label.strip() else ""
        token = token.strip(".,:!\"'")
        return token if token in SPECIALIST_INTENTS else "qa"

    async def handle(self, message: str) -> tuple[str, str]:
        """Xử lý 1 tin nhắn: trả về (intent đã chọn, câu trả lời của specialist)."""
        label = (await self.triage.run(message)).text
        intent = self.normalize_intent(label)
        reply = await self.specialists[intent].run(message)
        return intent, reply.text
