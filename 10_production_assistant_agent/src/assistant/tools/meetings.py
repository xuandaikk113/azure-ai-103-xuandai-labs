"""Tool đặt phòng họp — gọi mock API nội bộ (FastAPI ở mock_api/server.py).

Trong thực tế, thay endpoint mock bằng Microsoft Graph /events hoặc hệ thống booking thật.
"""

import httpx
from agent_framework import tool   # decorator biến hàm Python thành FunctionTool

from ..config import get_settings


@tool
def book_meeting(
    title: str,
    date: str,
    start_time: str,
    duration_minutes: int = 30,          # optional — mặc định 30 phút
    attendees: str = "",                 # optional — danh sách email, phân tách bằng dấu phẩy
) -> str:
    """Đặt một cuộc họp trong lịch nội bộ.

    Tham số:
      title: tiêu đề cuộc họp.
      date: ngày họp dạng YYYY-MM-DD.
      start_time: giờ bắt đầu dạng HH:MM (24h).
      duration_minutes: thời lượng phút (mặc định 30).
      attendees: email người tham dự, phân tách bằng dấu phẩy.
    """
    settings = get_settings()
    payload = {
        "title": title,
        "date": date,
        "start_time": start_time,
        "duration_minutes": duration_minutes,
        "attendees": [email.strip() for email in attendees.split(",") if email.strip()],
    }
    response = httpx.post(f"{settings.mock_api_base_url}/meetings", json=payload, timeout=10)
    response.raise_for_status()
    meeting = response.json()
    return (
        f"Đã đặt phòng họp '{title}' ngày {date} lúc {start_time} "
        f"({duration_minutes} phút), id={meeting['id']}."
    )
