"""
====================================================================
LAB 03/09 · Agent + Azure Functions tool (logic serverless qua Storage Queue)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry Agent Service + Azure Functions + Storage Queue
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL,
               STORAGE_QUEUE_SERVICE_ENDPOINT, STORAGE_INPUT_QUEUE_NAME, STORAGE_OUTPUT_QUEUE_NAME
SDK tiền nhiệm: azure-ai-agents -> azure-ai-projects 2.x.
Chạy         : uv run 03_build_and_deploy_agents/09_agent_azure_functions_tool.py
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
# Azure Functions tool: agent kích hoạt function serverless qua hàng đợi (queue) input/output.
from azure.ai.projects.models import (
    PromptAgentDefinition,
    AzureFunctionTool,
    AzureFunctionDefinition,
    AzureFunctionDefinitionFunction,
    AzureFunctionBinding,
    AzureFunctionStorageQueue,
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
        "STORAGE_QUEUE_SERVICE_ENDPOINT", "STORAGE_INPUT_QUEUE_NAME", "STORAGE_OUTPUT_QUEUE_NAME",
    )
    endpoint_queue = cfg["STORAGE_QUEUE_SERVICE_ENDPOINT"]

    tool = AzureFunctionTool(
        azure_function=AzureFunctionDefinition(
            # input_binding: agent đẩy yêu cầu vào queue này
            input_binding=AzureFunctionBinding(
                storage_queue=AzureFunctionStorageQueue(
                    queue_name=cfg["STORAGE_INPUT_QUEUE_NAME"],
                    queue_service_endpoint=endpoint_queue,
                )
            ),
            # output_binding: function trả kết quả qua queue này
            output_binding=AzureFunctionBinding(
                storage_queue=AzureFunctionStorageQueue(
                    queue_name=cfg["STORAGE_OUTPUT_QUEUE_NAME"],
                    queue_service_endpoint=endpoint_queue,
                )
            ),
            function=AzureFunctionDefinitionFunction(
                name="queue_trigger",
                description="Lấy thời tiết cho 1 địa điểm.",
                parameters={
                    "type": "object",
                    "properties": {"location": {"type": "string", "description": "địa điểm"}},
                },
            ),
        )
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"], credential=credential) as project,
    ):
        agent = project.agents.create_version(
            agent_name="ai103-func-agent",
            definition=PromptAgentDefinition(
                model=cfg["FOUNDRY_MODEL"],
                instructions="Dùng Azure Function để lấy thời tiết.",
                tools=[tool],
            ),
        )
        try:
            with project.get_openai_client(agent_name=agent.name) as openai_client:
                resp = openai_client.responses.create(input="Thời tiết Đà Nẵng?")
                print("Trả lời:", resp.output_text)
        finally:
            project.agents.delete_version(agent_name=agent.name, agent_version=agent.version, force=True)

    # Khác custom function (03/02, chạy in-process): Azure Functions tool chạy SERVERLESS, async qua queue.


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
