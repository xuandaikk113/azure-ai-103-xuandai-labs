"""Tập hợp tool cho các specialist agent.

Mỗi tool là 1 FunctionTool (decorate @tool): schema tham số tự suy ra từ type hints + docstring.
Các hàm logic cốt lõi (search_docs, sql_from_question, …) tách riêng khỏi @tool để UNIT TEST
được mà không cần LLM hay network.
"""

from .meetings import book_meeting
from .worklog import log_work
from .docsearch import search_internal_docs
from .websearch import search_web
from .sales_analytics import analyze_sales

__all__ = [
    "book_meeting",
    "log_work",
    "search_internal_docs",
    "search_web",
    "analyze_sales",
]
