"""
====================================================================
LAB 06/05 · Gắn Azure AI Search tool vào agent (RAG agentic có grounding)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry Agent Service + Azure AI Search
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL, AI_SEARCH_PROJECT_CONNECTION_ID, AZURE_SEARCH_INDEX
SDK tiền nhiệm: azure-ai-agents -> azure-ai-projects 2.x.
Chạy         : uv run 06_rag_and_foundry_iq_grounding/05_rag_connect_retrieval_to_agent_workflow.py
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
# AzureAISearchTool: cho agent truy vấn 1 index AI Search qua connection của project.
from azure.ai.projects.models import (
    PromptAgentDefinition,
    AzureAISearchTool,
    AzureAISearchToolResource,
    AISearchIndexResource,
    AzureAISearchQueryType,
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
    cfg = require_env(
        "FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL",
        "AI_SEARCH_PROJECT_CONNECTION_ID", "AZURE_SEARCH_INDEX",
    )

    tool = AzureAISearchTool(
        azure_ai_search=AzureAISearchToolResource(
            indexes=[
                AISearchIndexResource(
                    project_connection_id=cfg["AI_SEARCH_PROJECT_CONNECTION_ID"],
                    index_name=cfg["AZURE_SEARCH_INDEX"],
                    query_type=AzureAISearchQueryType.SIMPLE,
                ),
            ]
        )
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"], credential=credential) as project,
    ):
        agent = project.agents.create_version(
            agent_name="ai103-rag-agent",
            definition=PromptAgentDefinition(
                model=cfg["FOUNDRY_MODEL"],
                # Yêu cầu agent luôn trích dẫn nguồn -> grounding kiểm soát được
                instructions="Trả lời dựa trên AI Search và luôn kèm trích dẫn nguồn.",
                tools=[tool],
            ),
        )
        try:
            with project.get_openai_client(agent_name=agent.name) as openai_client:
                resp = openai_client.responses.create(input="Chính sách đổi trả hàng?")
                print("Trả lời (có grounding):", resp.output_text)
        finally:
            project.agents.delete_version(agent_name=agent.name, agent_version=agent.version, force=True)

    # Đây là RAG "agentic": agent TỰ quyết định truy vấn index khi cần, khác gọi search thủ công (06/01).


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
