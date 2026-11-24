"""
====================================================================
LAB 09/01 · Agent tracing bằng OpenTelemetry -> Application Insights
--------------------------------------------------------------------
Dịch vụ      : Microsoft Agent Framework + Azure Monitor (OpenTelemetry)
Biến .env    : APPLICATIONINSIGHTS_CONNECTION_STRING, FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: không.
Chạy         : uv run 09_observability_and_tracing/01_agent_tracing_opentelemetry.py
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

# ── Observability ───────────────────────────────────────────────
# azure-monitor-opentelemetry: nối OpenTelemetry với Application Insights (1 dòng cấu hình).
from azure.monitor.opentelemetry import configure_azure_monitor

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


async def main() -> None:
    cfg = require_env(
        "APPLICATIONINSIGHTS_CONNECTION_STRING", "FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL",
    )

    # Bật xuất trace/metric/log lên Application Insights.
    # Agent Framework phát span OpenTelemetry -> tự động gửi qua exporter này.
    configure_azure_monitor(connection_string=cfg["APPLICATIONINSIGHTS_CONNECTION_STRING"])

    agent = Agent(
        client=FoundryChatClient(
            project_endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
            model=cfg["FOUNDRY_MODEL"],
            credential=DefaultAzureCredential(),
        ),
        name="ai103-traced-agent",
        instructions="Bạn là trợ lý tiếng Việt.",
    )

    result = await agent.run("Giải thích observability trong 1 câu.")
    print("Trả lời:", result.text)
    print("\nTrace đã gửi lên Application Insights: xem token, latency, tool calls, safety signals.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
