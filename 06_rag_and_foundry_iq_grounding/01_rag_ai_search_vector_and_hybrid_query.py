"""
====================================================================
LAB 06/01 · Azure AI Search: vector + hybrid query
--------------------------------------------------------------------
Dịch vụ      : Azure AI Search + Azure OpenAI (embedding)
Biến .env    : AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, AZURE_SEARCH_INDEX,
               AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_EMBEDDING_DEPLOYMENT (v1: bỏ api_version)
SDK tiền nhiệm: Azure Cognitive Search -> Azure AI Search (azure-search-documents).
Chạy         : uv run 06_rag_and_foundry_iq_grounding/01_rag_ai_search_vector_and_hybrid_query.py
Giả định     : index có field 'contentVector' (vector) và 'content' (text).
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
from azure.core.credentials import AzureKeyCredential

# ── SDK ─────────────────────────────────────────────────────────
from azure.search.documents import SearchClient
# VectorizedQuery: truy vấn bằng vector đã tính sẵn (ta tự tạo embedding).
from azure.search.documents.models import VectorizedQuery
from openai import OpenAI   # tạo embedding cho câu truy vấn (client v1 khuyến nghị)


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
        "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_API_KEY", "AZURE_SEARCH_INDEX",
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    )
    query = "Chính sách đổi trả hàng thế nào?"

    # 1) Tạo embedding cho câu truy vấn (text -> vector)
    aoai = OpenAI(
        base_url=cfg["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1/",
        api_key=cfg["AZURE_OPENAI_API_KEY"],
    )
    embedding = aoai.embeddings.create(
        model=cfg["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"], input=query,
    ).data[0].embedding

    # 2) HYBRID = search_text (BM25 từ khoá) + vector_queries (ngữ nghĩa) cùng lúc
    search_client = SearchClient(
        endpoint=cfg["AZURE_SEARCH_ENDPOINT"],
        index_name=cfg["AZURE_SEARCH_INDEX"],
        credential=AzureKeyCredential(cfg["AZURE_SEARCH_API_KEY"]),
    )
    vector_query = VectorizedQuery(
        vector=embedding, k_nearest_neighbors=3, fields="contentVector",
    )
    results = search_client.search(
        search_text=query,                 # phần keyword (BM25)
        vector_queries=[vector_query],     # phần vector (ngữ nghĩa)
        top=3,
    )

    # 3) In kết quả + điểm số
    for doc in results:
        print(f"[score={doc['@search.score']:.3f}] {doc.get('content', '')[:80]}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
