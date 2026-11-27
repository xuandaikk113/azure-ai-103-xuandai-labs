"""Trợ lý production-ready (Microsoft Agent Framework + handoff orchestration).

Kiến trúc: triage agent phân loại intent -> handoff sang specialist agent tương ứng.
Specialist dùng các tool (mock API đặt phòng/log work, tra tài liệu nội bộ, web search,
phân tích DB bán hàng text2sql + chart).
"""
