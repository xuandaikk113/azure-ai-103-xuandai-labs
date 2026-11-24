"""
====================================================================
LAB 03/03 · Built-in tools: Code Interpreter + File Search
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry Agent Service
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: azure-ai-agents -> azure-ai-projects 2.x.
Chạy         : uv run 03_build_and_deploy_agents/03_agent_with_code_interpreter_and_file_search.py
Cần          : file mẫu assets/product_info.md (để File Search index)
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
# CodeInterpreterTool: chạy code (tính toán/biểu đồ). FileSearchTool: tra cứu file đã index.
from azure.ai.projects.models import PromptAgentDefinition, CodeInterpreterTool, FileSearchTool


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
    file_path = os.path.join("assets", "product_info.md")
    if not os.path.exists(file_path):
        sys.exit(f"[THIẾU DỮ LIỆU] Tạo file: {file_path}")

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"], credential=credential) as project,
        project.get_openai_client() as openai_client,
    ):
        # 1) Tạo vector store + upload file (File Search cần vector store)
        vector_store = openai_client.vector_stores.create(name="ai103-product-store")
        with open(file_path, "rb") as f:
            openai_client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store.id, file=f,
            )
        print(f"Đã index file vào vector store {vector_store.id}")

        # 2) Tạo agent gắn CẢ 2 built-in tool
        agent = project.agents.create_version(
            agent_name="ai103-tools-agent",
            definition=PromptAgentDefinition(
                model=cfg["FOUNDRY_MODEL"],
                instructions="Dùng code interpreter để tính toán và file search để tra tài liệu.",
                tools=[CodeInterpreterTool(), FileSearchTool(vector_store_ids=[vector_store.id])],
            ),
        )
        try:
            # 3) Hỏi câu cần tính toán (code interpreter)
            r1 = openai_client.responses.create(
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                input="Tính tổng 123 + 456 rồi nhân 2.",
            )
            print("Tính toán:", r1.output_text)

            # 4) Hỏi câu cần tra file (file search)
            r2 = openai_client.responses.create(
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                input="Tóm tắt thông tin sản phẩm trong tài liệu.",
            )
            print("Tra tài liệu:", r2.output_text)
        finally:
            project.agents.delete_version(agent_name=agent.name, agent_version=agent.version, force=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
