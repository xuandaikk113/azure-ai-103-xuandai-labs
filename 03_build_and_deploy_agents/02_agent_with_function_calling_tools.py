"""
====================================================================
LAB 03/02 · Agent + Function calling (custom tool) + vòng lặp tool-call
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry Agent Service
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: azure-ai-agents -> azure-ai-projects 2.x.
Chạy         : uv run 03_build_and_deploy_agents/02_agent_with_function_calling_tools.py
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import json                     # parse arguments của tool-call & đóng gói kết quả

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
from azure.ai.projects.models import PromptAgentDefinition, FunctionTool
# FunctionCallOutput: kiểu message trả KẾT QUẢ hàm về cho model (Responses API).
from openai.types.responses.response_input_param import FunctionCallOutput


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


# ── Hàm thật mà agent sẽ gọi ────────────────────────────────────
def get_exchange_rate(currency: str) -> str:
    """Tra tỷ giá (giả lập) cho 1 loại tiền sang VND."""
    rates = {"USD": "25.400", "EUR": "27.100", "JPY": "165"}
    return rates.get(currency.upper(), "không rõ")


def main() -> None:
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")

    # Khai báo tool theo JSON schema (strict=True để model tuân thủ tham số)
    tool = FunctionTool(
        name="get_exchange_rate",
        description="Lấy tỷ giá 1 loại tiền sang VND.",
        parameters={
            "type": "object",
            "properties": {"currency": {"type": "string", "description": "Mã tiền, vd USD"}},
            "required": ["currency"],
            "additionalProperties": False,
        },
        strict=True,
    )

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"], credential=credential) as project,
    ):
        agent = project.agents.create_version(
            agent_name="ai103-function-agent",
            definition=PromptAgentDefinition(
                model=cfg["FOUNDRY_MODEL"],
                instructions="Bạn là trợ lý tài chính, dùng tool khi cần số liệu.",
                tools=[tool],
            ),
        )
        try:
            with project.get_openai_client(agent_name=agent.name) as openai_client:
                response = openai_client.responses.create(input="1 USD bằng bao nhiêu VND?")

                # ── Vòng lặp tool-call: lặp tới khi model không còn gọi hàm ──
                while True:
                    tool_outputs = []
                    for item in response.output:
                        if item.type == "function_call" and item.name == "get_exchange_rate":
                            args = json.loads(item.arguments)           # tham số model gửi
                            result = get_exchange_rate(**args)          # chạy hàm Python thật
                            tool_outputs.append(FunctionCallOutput(
                                type="function_call_output",
                                call_id=item.call_id,
                                output=json.dumps({"rate": result}),
                            ))
                    if not tool_outputs:
                        break                                           # hết tool-call -> xong
                    # gửi kết quả hàm về, nối phiên bằng previous_response_id
                    response = openai_client.responses.create(
                        input=tool_outputs, previous_response_id=response.id,
                    )

                print("Trả lời:", response.output_text)
        finally:
            project.agents.delete_version(
                agent_name=agent.name, agent_version=agent.version, force=True,
            )

    # Ghi chú: muốn phê duyệt thủ công hành động nhạy cảm -> dùng require_approval
    # (thấy rõ ở tool MCP, lab 03/04).


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
