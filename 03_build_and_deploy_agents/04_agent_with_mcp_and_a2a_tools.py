"""
====================================================================
LAB 03/04 · Agent + MCP tool (+ ghi chú A2A)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry Agent Service
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL, MCP_SERVER_URL
SDK tiền nhiệm: azure-ai-agents -> azure-ai-projects 2.x.
Chạy         : uv run 03_build_and_deploy_agents/04_agent_with_mcp_and_a2a_tools.py
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
# MCPTool: kết nối agent tới 1 MCP server (Model Context Protocol - chuẩn mở chia sẻ tool/data).
from azure.ai.projects.models import PromptAgentDefinition, MCPTool
# McpApprovalResponse: message gửi lại để PHÊ DUYỆT lời gọi tool MCP.
from openai.types.responses.response_input_param import McpApprovalResponse


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
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL", "MCP_SERVER_URL")

    # require_approval="always" -> mỗi lần gọi tool MCP phải được phê duyệt (an toàn).
    mcp_tool = MCPTool(
        server_label="api-specs",
        server_url=cfg["MCP_SERVER_URL"],
        require_approval="always",
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"], credential=credential) as project,
    ):
        agent = project.agents.create_version(
            agent_name="ai103-mcp-agent",
            definition=PromptAgentDefinition(
                model=cfg["FOUNDRY_MODEL"],
                instructions="Dùng các tool MCP để trả lời câu hỏi kỹ thuật.",
                tools=[mcp_tool],
            ),
        )
        try:
            with project.get_openai_client(agent_name=agent.name) as openai_client:
                response = openai_client.responses.create(input="Liệt kê vài REST API của Azure.")

                # ── Vòng lặp PHÊ DUYỆT: model xin phép -> ta chấp thuận -> chạy tiếp ──
                while True:
                    approvals = []
                    for item in response.output:
                        if item.type == "mcp_approval_request":
                            approvals.append(McpApprovalResponse(
                                type="mcp_approval_response",
                                approve=True,                 # phê duyệt (thực tế nên kiểm tra kỹ)
                                approval_request_id=item.id,
                            ))
                    if not approvals:
                        break
                    response = openai_client.responses.create(
                        input=approvals, previous_response_id=response.id,
                    )

                print("Trả lời:", response.output_text)
        finally:
            project.agents.delete_version(agent_name=agent.name, agent_version=agent.version, force=True)

    # A2A (Agent-to-Agent): một agent gọi agent khác như một endpoint từ xa. Mô hình tương tự
    # tool ở đây nhưng "tool" là một agent khác -> dùng để phối hợp agent giữa các hệ thống.


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
