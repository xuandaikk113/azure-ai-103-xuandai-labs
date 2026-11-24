"""
====================================================================
LAB 08/03 · Content Understanding: prebuilt document analyzer
--------------------------------------------------------------------
Dịch vụ      : Azure AI Content Understanding (SDK GA 1.1.0)
Biến .env    : CONTENT_UNDERSTANDING_ENDPOINT, CONTENT_UNDERSTANDING_API_KEY
SDK tiền nhiệm: trước khi có SDK phải gọi REST thủ công bằng requests.
Chạy         : uv run 08_information_extraction/03_content_understanding_prebuilt_document_analyzer.py
Lưu ý        : CU nhận input qua URL (blob + SAS). Cần cấu hình default-model một lần (gpt-4.1,
               text-embedding-3-large) + role Cognitive Services User trước khi dùng prebuilt.
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

# ── SDK Content Understanding ───────────────────────────────────
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import AnalysisInput, AnalysisResult

# Thay bằng URL tài liệu của bạn (blob public hoặc có SAS token)
SAMPLE_DOC_URL = "https://<your-blob>/documents/sample.pdf"


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
    cfg = require_env("CONTENT_UNDERSTANDING_ENDPOINT", "CONTENT_UNDERSTANDING_API_KEY")
    client = ContentUnderstandingClient(
        endpoint=cfg["CONTENT_UNDERSTANDING_ENDPOINT"],
        credential=AzureKeyCredential(cfg["CONTENT_UNDERSTANDING_API_KEY"]),
    )

    # begin_analyze: chọn analyzer prebuilt + truyền input qua URL (long-running)
    poller = client.begin_analyze(
        analyzer_id="prebuilt-documentSearch",
        inputs=[AnalysisInput(url=SAMPLE_DOC_URL)],
    )
    result: AnalysisResult = poller.result()

    # result.contents[0]: nội dung đã trích; .markdown là biểu diễn sạch cho RAG/agent
    content = result.contents[0]
    print("Markdown:\n", content.markdown[:500])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
