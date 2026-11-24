"""
====================================================================
LAB 03/08 · Agent + OpenAPI spec tool (gọi REST API ngoài)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry Agent Service
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: azure-ai-agents -> azure-ai-projects 2.x.
Chạy         : uv run 03_build_and_deploy_agents/08_agent_openapi_spec_tool.py
Cần          : file spec assets/weather_openapi.json (OpenAPI 3.x)
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import json                     # nạp file OpenAPI spec (JSON)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── xác thực ────────────────────────────────────────────────────
from azure.identity import DefaultAzureCredential

# ── SDK Foundry agents ──────────────────────────────────────────
from azure.ai.projects import AIProjectClient
# OpenApiTool: biến 1 OpenAPI spec thành tool; agent tự gọi REST theo spec.
from azure.ai.projects.models import (
    PromptAgentDefinition,
    OpenApiTool,
    OpenApiFunctionDefinition,
    OpenApiAnonymousAuthDetails,   # API không cần auth; có loại khác cho API key/OAuth
)


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def main() -> None:
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")

    spec_path = os.path.join("assets", "weather_openapi.json")
    if not os.path.exists(spec_path):
        sys.exit(f"[THIẾU DỮ LIỆU] Tạo file OpenAPI tại: {spec_path}")
    # Nếu spec dùng $ref, cài 'jsonref' và dùng jsonref.loads để giải tham chiếu.
    with open(spec_path, encoding="utf-8") as f:
        openapi_spec = json.load(f)

    tool = OpenApiTool(
        openapi=OpenApiFunctionDefinition(
            name="get_weather",
            spec=openapi_spec,
            description="Lấy thông tin thời tiết theo địa điểm.",
            auth=OpenApiAnonymousAuthDetails(),
        )
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"], credential=credential) as project,
    ):
        agent = project.agents.create_version(
            agent_name="ai103-openapi-agent",
            definition=PromptAgentDefinition(
                model=cfg["FOUNDRY_MODEL"],
                instructions="Dùng tool OpenAPI để trả lời câu hỏi thời tiết.",
                tools=[tool],
            ),
        )
        try:
            with project.get_openai_client(agent_name=agent.name) as openai_client:
                resp = openai_client.responses.create(input="Thời tiết ở Hà Nội thế nào?")
                print("Trả lời:", resp.output_text)
        finally:
            project.agents.delete_version(agent_name=agent.name, agent_version=agent.version, force=True)

    # OpenAPI tool = tích hợp API có sẵn KHÔNG cần viết code wrapper; auth khai trong spec/tool.


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
