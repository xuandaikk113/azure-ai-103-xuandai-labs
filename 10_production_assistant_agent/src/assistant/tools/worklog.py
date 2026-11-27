"""Tool ghi nhận công việc (log work) — gọi mock API nội bộ.

Thực tế thay bằng API chấm công / Jira / Azure DevOps work items.
"""

from datetime import date as date_type

import httpx
from agent_framework import tool

from ..config import get_settings


@tool
def log_work(
    task: str,
    hours: float,
    work_date: str = "",                 # optional — mặc định hôm nay (YYYY-MM-DD)
    note: str = "",                      # optional — ghi chú thêm
) -> str:
    """Ghi nhận thời gian làm việc cho một task.

    Tham số:
      task: tên/mô tả công việc.
      hours: số giờ đã làm (vd 1.5).
      work_date: ngày làm việc YYYY-MM-DD (mặc định hôm nay nếu bỏ trống).
      note: ghi chú tuỳ chọn.
    """
    settings = get_settings()
    payload = {
        "task": task,
        "hours": hours,
        "work_date": work_date or date_type.today().isoformat(),
        "note": note,
    }
    response = httpx.post(f"{settings.mock_api_base_url}/worklog", json=payload, timeout=10)
    response.raise_for_status()
    entry = response.json()
    return f"Đã log {hours}h cho '{task}' ngày {payload['work_date']} (id={entry['id']})."
