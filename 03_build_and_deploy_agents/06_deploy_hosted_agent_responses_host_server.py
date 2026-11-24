"""
====================================================================
LAB 03/06 · Host agent thành HTTP endpoint /responses (hosted agent)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework + HTTP server
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL, PORT
SDK tiền nhiệm: không.
Chạy         : uv run 03_build_and_deploy_agents/06_deploy_hosted_agent_responses_host_server.py
Lưu ý        : Đây là HOST tối giản (stdlib) để HIỂU cách hosted agent nói "ngôn ngữ" Responses.
               Khi deploy thật lên Foundry Hosted Agent, dùng host có sẵn của agent-framework
               (DevUI / Responses host) — tra Microsoft Learn cho API hosting chính thức.
Test         : curl -X POST localhost:8080/responses -d '{"input":"xin chào"}'
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import json
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer   # HTTP server tối giản

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


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def build_agent(cfg: dict) -> Agent:
    """Tạo agent (dựng 1 lần, dùng lại cho mọi request)."""
    return Agent(
        client=FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=DefaultAzureCredential(),
        ),
        name="ai103-hosted-agent",
        instructions="Bạn là trợ lý tiếng Việt.",
    )


def make_handler(agent: Agent):
    """Tạo lớp handler đóng gói sẵn agent."""
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):   # xử lý POST /responses
            if self.path != "/responses":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            # Gọi agent (chạy coroutine trong event loop mới cho mỗi request)
            result = asyncio.run(agent.run(body.get("input", "")))
            payload = json.dumps({"output_text": result.text}, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(payload)
    return Handler


def main() -> None:
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL", "PORT")
    agent = build_agent(cfg)
    port = int(cfg["PORT"])
    server = HTTPServer(("0.0.0.0", port), make_handler(agent))
    print(f"Hosted agent chạy tại http://localhost:{port}/responses  (Ctrl+C để dừng)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng server.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
