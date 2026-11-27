"""HTTP host cho trợ lý — expose POST /responses (chuẩn hoá output_text như Foundry Hosted Agent).

Chạy: uv run uvicorn assistant.host:app --port 8080
Deploy: đóng gói bằng Dockerfile -> Azure Container Apps (xem deploy/ và README).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from .config import get_settings
from .chat_client import build_chat_client
from .router import AssistantRouter

_router: AssistantRouter | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dựng router (model client + agents) 1 lần lúc khởi động, tái dùng cho mọi request.
    global _router
    _router = AssistantRouter(build_chat_client(get_settings()))
    yield


app = FastAPI(title="Production Assistant Agent", lifespan=lifespan)


class ResponseRequest(BaseModel):
    input: str   # tin nhắn người dùng


@app.get("/health")
def health() -> dict:
    """Health probe cho Container Apps / load balancer."""
    return {"status": "ok"}


@app.post("/responses")
async def responses(body: ResponseRequest) -> dict:
    """Nhận input, handoff qua router, trả output_text + intent đã định tuyến."""
    assert _router is not None, "Router chưa khởi tạo"
    intent, reply = await _router.handle(body.input)
    return {"output_text": reply, "intent": intent}
