"""
====================================================================
LAB 06/04 · Foundry IQ: Agentic Retrieval (knowledge base)
--------------------------------------------------------------------
Dịch vụ      : Azure AI Search (Foundry IQ / knowledge base)
Biến .env    : AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KNOWLEDGE_BASE
SDK tiền nhiệm: RAG tự viết query -> Foundry IQ TỰ lập kế hoạch truy vấn (agentic).
Chạy         : uv run 06_rag_and_foundry_iq_grounding/04_rag_foundry_iq_agentic_retrieval.py
⚠ Lưu ý      : Đây là API 2026 MỚI. Tên class (KnowledgeBaseRetrievalClient) đúng, nhưng
               ĐƯỜNG DẪN IMPORT và các model request có thể khác — đối chiếu quickstart
               "Agentic retrieval" trên Microsoft Learn khi chạy thật.
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

# ── xác thực (knowledge base dùng Entra ID) ─────────────────────
from azure.identity import DefaultAzureCredential

# ── SDK (agentic retrieval - azure-search-documents) ────────────
# KnowledgeBaseRetrievalClient: client truy hồi từ 1 knowledge base của Foundry IQ.
# (Đường dẫn import dưới đây theo cấu trúc dự kiến — xác minh lại với quickstart.)
from azure.search.documents.agent import KnowledgeBaseRetrievalClient
from azure.search.documents.agent.models import (
    KnowledgeBaseRetrievalRequest,
    KnowledgeBaseMessage,
    KnowledgeBaseMessageTextContent,
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
    cfg = require_env("AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_KNOWLEDGE_BASE")

    # Client trỏ tới 1 knowledge base (đã tạo trước trên Azure AI Search / Foundry IQ)
    client = KnowledgeBaseRetrievalClient(
        endpoint=cfg["AZURE_SEARCH_ENDPOINT"],
        knowledge_base_name=cfg["AZURE_SEARCH_KNOWLEDGE_BASE"],
        credential=DefaultAzureCredential(),
    )

    # Agentic retrieval: gửi câu hỏi ở dạng message; Foundry IQ TỰ lập kế hoạch truy vấn
    # đa nguồn, áp quyền người dùng, rồi trả câu trả lời có citation.
    request = KnowledgeBaseRetrievalRequest(
        messages=[
            KnowledgeBaseMessage(
                role="user",
                content=[KnowledgeBaseMessageTextContent(text="Chính sách bảo hành sản phẩm?")],
            )
        ],
        include_activity=True,   # trả thêm 'activity' để thấy các bước truy vấn
    )
    result = client.retrieve(retrieval_request=request)

    # In nội dung đã grounding (có trích dẫn nguồn)
    print("Kết quả agentic retrieval:")
    print(result)

    # Mẹo: 'retrieval_reasoning_effort' cao hơn -> truy vấn kỹ hơn nhưng tốn/chậm hơn.
    # 'minimal' chỉ dùng semantic (không LLM).


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
