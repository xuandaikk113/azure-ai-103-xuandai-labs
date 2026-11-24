"""
====================================================================
LAB 03/01 · Prompt Agent trên Foundry Agent Service
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry Agent Service
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: azure-ai-agents (gói riêng, create_agent) -> ĐÃ GỘP vào azure-ai-projects 2.x (create_version).
Chạy         : uv run 03_build_and_deploy_agents/01_agent_foundry_service_prompt_agent.py
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

# ── xác thực keyless (AIProjectClient chỉ hỗ trợ Entra ID) ──────
from azure.identity import DefaultAzureCredential

# ── SDK Foundry project + agents ────────────────────────────────
from azure.ai.projects import AIProjectClient
# PromptAgentDefinition: định nghĩa 1 agent (model + instructions + tools).
from azure.ai.projects.models import PromptAgentDefinition


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

    # with ...: tự đóng credential & client khi xong
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"], credential=credential) as project,
    ):
        # 1) Tạo 1 version của agent (server-managed)
        agent = project.agents.create_version(
            agent_name="ai103-prompt-agent",
            definition=PromptAgentDefinition(
                model=cfg["FOUNDRY_MODEL"],
                instructions="Bạn là trợ lý tiếng Việt, trả lời ngắn gọn và chính xác.",
            ),
        )
        print(f"Đã tạo agent: name={agent.name}, version={agent.version}")

        try:
            # 2) Gọi agent qua Responses API (lấy client openai gắn với agent)
            with project.get_openai_client(agent_name=agent.name) as openai_client:
                resp = openai_client.responses.create(input="Foundry Agent Service là gì?")
                print("Trả lời:", resp.output_text)
        finally:
            # 3) Dọn dẹp: xoá version agent test
            project.agents.delete_version(
                agent_name=agent.name, agent_version=agent.version, force=True,
            )
            print("Đã xoá agent test.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
