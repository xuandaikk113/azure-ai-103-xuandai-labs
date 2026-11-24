"""
====================================================================
LAB 03/07 · Agent + Grounding with Bing (web search tool)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry Agent Service + Bing grounding
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL, BING_PROJECT_CONNECTION_ID
SDK tiền nhiệm: azure-ai-agents -> azure-ai-projects 2.x.
Chạy         : uv run 03_build_and_deploy_agents/07_agent_bing_grounding_tool.py
Lưu ý        : Bing grounding có CHI PHÍ & điều khoản riêng; dữ liệu rời khỏi ranh giới tuân thủ Azure.
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys

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
# Bing grounding tool: cần 1 connection "Grounding with Bing" trong project (tab Connections).
from azure.ai.projects.models import (
    PromptAgentDefinition,
    BingGroundingTool,
    BingGroundingSearchToolParameters,
    BingGroundingSearchConfiguration,
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
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL", "BING_PROJECT_CONNECTION_ID")

    tool = BingGroundingTool(
        bing_grounding=BingGroundingSearchToolParameters(
            search_configurations=[
                BingGroundingSearchConfiguration(
                    project_connection_id=cfg["BING_PROJECT_CONNECTION_ID"],
                )
            ]
        )
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"], credential=credential) as project,
    ):
        agent = project.agents.create_version(
            agent_name="ai103-bing-agent",
            definition=PromptAgentDefinition(
                model=cfg["FOUNDRY_MODEL"],
                instructions="Trả lời dựa trên kết quả web mới nhất, kèm nguồn.",
                tools=[tool],
            ),
        )
        try:
            with project.get_openai_client(agent_name=agent.name) as openai_client:
                resp = openai_client.responses.create(input="Tin công nghệ nổi bật tuần này là gì?")
                print("Trả lời:", resp.output_text)
                # Grounding Bing thường đính kèm url_citation trong annotations của output.
        finally:
            project.agents.delete_version(agent_name=agent.name, agent_version=agent.version, force=True)

    # So sánh: Bing grounding = tri thức WEB bên ngoài; khác RAG nội bộ (Azure AI Search, folder 06).


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
