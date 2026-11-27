"""Mock API nội bộ (FastAPI) — thay cho hệ thống đặt phòng họp & chấm công thật.

Lưu trong bộ nhớ (reset khi restart) — đủ để demo offline. Thực tế thay bằng
Microsoft Graph / Jira / Azure DevOps.

Chạy: uv run uvicorn mock_api.server:app --port 8000
"""

import itertools

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock Internal APIs")

_meeting_id_seq = itertools.count(1)
_worklog_id_seq = itertools.count(1)
_meetings: list[dict] = []
_worklog: list[dict] = []


class Meeting(BaseModel):
    title: str
    date: str
    start_time: str
    duration_minutes: int = 30
    attendees: list[str] = []


class WorkLog(BaseModel):
    task: str
    hours: float
    work_date: str
    note: str = ""


@app.post("/meetings")
def create_meeting(meeting: Meeting) -> dict:
    record = {"id": next(_meeting_id_seq), **meeting.model_dump()}
    _meetings.append(record)
    return record


@app.post("/worklog")
def create_worklog(entry: WorkLog) -> dict:
    record = {"id": next(_worklog_id_seq), **entry.model_dump()}
    _worklog.append(record)
    return record


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "meetings": len(_meetings), "worklog": len(_worklog)}
