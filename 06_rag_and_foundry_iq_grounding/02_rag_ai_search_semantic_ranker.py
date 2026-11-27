"""
====================================================================
LAB 06/02 · Azure AI Search: Semantic Ranker (rerank + captions/answers)
--------------------------------------------------------------------
Dịch vụ      : Azure AI Search
Biến .env    : AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, AZURE_SEARCH_INDEX, AZURE_SEARCH_SEMANTIC_CONFIG
SDK tiền nhiệm: Azure Cognitive Search -> Azure AI Search.
Chạy         : uv run 06_rag_and_foundry_iq_grounding/02_rag_ai_search_semantic_ranker.py
Giả định     : index đã cấu hình 1 semantic configuration (tên lưu ở AZURE_SEARCH_SEMANTIC_CONFIG).
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
# QueryType/QueryCaptionType/QueryAnswerType: bật semantic + captions/answers.
from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType


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
        "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX", "AZURE_SEARCH_SEMANTIC_CONFIG",
    )
    search_client = SearchClient(
        endpoint=cfg["AZURE_SEARCH_ENDPOINT"],
        index_name=cfg["AZURE_SEARCH_INDEX"],
        credential=AzureKeyCredential(cfg["AZURE_SEARCH_API_KEY"]),
    )
    # ── Alternative KEYLESS (Entra ID, khuyến nghị production) — thay cho AzureKeyCredential ──
    #   from azure.identity import DefaultAzureCredential
    #   search_client = SearchClient(
    #       endpoint=cfg["AZURE_SEARCH_ENDPOINT"],
    #       index_name=cfg["AZURE_SEARCH_INDEX"],
    #       credential=DefaultAzureCredential(),
    #   )
    #   (keyless chạy được khi principal có đúng RBAC data-plane role cho Search —
    #    vd Search Index Data Reader (đọc) / Search Index Data Contributor (ghi); xem lab 00/04)

    # Semantic ranker: xếp hạng lại (L2) top kết quả + trích caption/answer
    results = search_client.search(
        search_text="Làm sao để đổi trả hàng?",
        query_type=QueryType.SEMANTIC,                               # bật semantic ranking
        semantic_configuration_name=cfg["AZURE_SEARCH_SEMANTIC_CONFIG"],
        query_caption=QueryCaptionType.EXTRACTIVE,                   # trích caption nổi bật
        query_answer=QueryAnswerType.EXTRACTIVE,                     # rút câu trả lời trực tiếp
        top=3,
    )

    # Câu trả lời trực tiếp (nếu có)
    for answer in results.get_answers() or []:
        print(f"[ANSWER] {answer.text}")

    # Kết quả đã rerank: đọc reranker_score (L2) + caption
    for doc in results:
        print(f"[reranker={doc['@search.reranker_score']:.3f}] {doc.get('content', '')[:60]}")
        for caption in doc.get("@search.captions", []) or []:
            print(f"    caption: {caption.text}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
