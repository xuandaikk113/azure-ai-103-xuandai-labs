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
        # 1) Tạo vector store rồi nạp file cho File Search.
        vector_store = openai_client.vector_stores.create(name="ai103-product-store")

        # 1a) CÁCH 1 · upload TỪNG file (đơn giản khi chỉ có 1 vài file)
        with open(file_path, "rb") as single_file:
            openai_client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store.id, file=single_file,
            )

        # 1b) CÁCH 2 · upload NHIỀU file 1 lần bằng FILE BATCHES
        #     Thực tế hay gặp: tài liệu nằm rải rác hoặc gom trong 1 thư mục.
        #     file_batches.upload_and_poll nhận cả LIST file handle, upload + index rồi poll tới xong.
        document_dir = "assets"
        batch_file_paths = [
            os.path.join(document_dir, name)
            for name in os.listdir(document_dir)
            if name.lower().endswith((".md", ".txt", ".pdf", ".docx"))
        ]
        file_handles = [open(path, "rb") for path in batch_file_paths]
        try:
            file_batch = openai_client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id,
                files=file_handles,
            )
            print(f"Đã index batch {len(batch_file_paths)} file — "
                  f"status={file_batch.status}, counts={file_batch.file_counts}")
        finally:
            for handle in file_handles:   # luôn đóng mọi file handle đã mở
                handle.close()
        print(f"Vector store sẵn sàng: {vector_store.id}")

        # 2) Tạo agent gắn CẢ 2 built-in tool.
        # CÁCH A · khai báo tool bằng CLASS (type-safe, gợi ý IDE):
        tools = [
            CodeInterpreterTool(),
            FileSearchTool(vector_store_ids=[vector_store.id]),
        ]
        # CÁCH B · khai báo tool bằng DICT (JSON thuần) — TƯƠNG ĐƯƠNG hệt cách A
        # (chính là dạng serialize của object ở trên). Tiện khi nạp cấu hình tool
        # từ file JSON/DB thay vì hard-code bằng class:
        #   tools = [
        #       {"type": "code_interpreter"},
        #       {"type": "file_search", "vector_store_ids": [vector_store.id]},
        #   ]
        agent = project.agents.create_version(
            agent_name="ai103-tools-agent",
            definition=PromptAgentDefinition(
                model=cfg["FOUNDRY_MODEL"],
                instructions="Dùng code interpreter để tính toán và file search để tra tài liệu.",
                tools=tools,
            ),
        )
        try:
            # 3) Hỏi câu cần tính toán (code interpreter)
            calculation_response = openai_client.responses.create(
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                input="Tính tổng 123 + 456 rồi nhân 2.",
            )
            print("Tính toán:", calculation_response.output_text)

            # 4) Hỏi câu cần tra file (file search)
            document_response = openai_client.responses.create(
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                input="Tóm tắt thông tin sản phẩm trong tài liệu.",
            )
            print("Tra tài liệu:", document_response.output_text)
        finally:
            project.agents.delete_version(agent_name=agent.name, agent_version=agent.version, force=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
