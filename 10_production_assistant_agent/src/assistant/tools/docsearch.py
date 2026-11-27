"""Tool tìm kiếm tài liệu nội bộ — retrieval local trên data/internal_docs/*.md.

Cố tình dùng thuật toán chấm điểm từ khoá đơn giản (không gọi dịch vụ ngoài) để chạy offline.
Production thật nên thay bằng Azure AI Search (vector/hybrid) — xem chương 06.
"""

import re
from pathlib import Path

from agent_framework import tool

from ..config import get_settings


def _tokenize(text: str) -> list[str]:
    """Tách từ, hạ chữ thường — đủ dùng cho chấm điểm overlap đơn giản."""
    return re.findall(r"\w+", text.lower())


def search_docs(query: str, docs_dir: str, top_k: int = 2) -> list[tuple[str, str, float]]:
    """Trả về top_k (tên file, đoạn trích, điểm) khớp nhất với query.

    Hàm thuần (không @tool) để unit test không cần LLM/network.
    # ponytail: chấm điểm bằng overlap từ khoá (O(n) trên số file nhỏ); nâng lên AI Search khi corpus lớn.
    """
    query_terms = set(_tokenize(query))
    if not query_terms:
        return []

    scored: list[tuple[str, str, float]] = []
    for path in sorted(Path(docs_dir).glob("*.md")):
        content = path.read_text(encoding="utf-8")
        doc_terms = _tokenize(content)
        if not doc_terms:
            continue
        overlap = sum(1 for term in doc_terms if term in query_terms)
        score = overlap / len(doc_terms)   # chuẩn hoá theo độ dài để file dài không thắng oan
        if overlap > 0:
            snippet = content.strip().replace("\n", " ")[:200]
            scored.append((path.name, snippet, score))

    scored.sort(key=lambda item: item[2], reverse=True)
    return scored[:top_k]


@tool
def search_internal_docs(query: str, top_k: int = 2) -> str:
    """Tra cứu tài liệu nội bộ (chính sách, hướng dẫn) theo câu hỏi.

    Tham số:
      query: câu hỏi hoặc từ khoá cần tra.
      top_k: số tài liệu trả về (mặc định 2).
    """
    settings = get_settings()
    results = search_docs(query, settings.internal_docs_dir, top_k=top_k)
    if not results:
        return "Không tìm thấy tài liệu nội bộ phù hợp."
    lines = [f"- {name}: {snippet}…" for name, snippet, _ in results]
    return "Tài liệu liên quan:\n" + "\n".join(lines)
