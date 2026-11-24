"""
====================================================================
LAB 08/01 · Document Intelligence: Layout + Tables
--------------------------------------------------------------------
Dịch vụ      : Azure AI Document Intelligence (prebuilt-layout)
Biến .env    : DOC_INTELLIGENCE_ENDPOINT, DOC_INTELLIGENCE_API_KEY
SDK tiền nhiệm: Form Recognizer (azure-ai-formrecognizer) -> azure-ai-documentintelligence.
Chạy         : uv run 08_information_extraction/01_doc_intelligence_layout_and_tables.py
Cần          : file assets/sample_document.pdf
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

# ── SDK Document Intelligence ───────────────────────────────────
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult


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
    cfg = require_env("DOC_INTELLIGENCE_ENDPOINT", "DOC_INTELLIGENCE_API_KEY")
    path = os.path.join("assets", "sample_document.pdf")
    if not os.path.exists(path):
        sys.exit(f"[THIẾU DỮ LIỆU] Đặt file tại: {path}")

    client = DocumentIntelligenceClient(
        cfg["DOC_INTELLIGENCE_ENDPOINT"], AzureKeyCredential(cfg["DOC_INTELLIGENCE_API_KEY"]),
    )

    # prebuilt-layout: trích cấu trúc trang, đoạn, BẢNG, toạ độ
    with open(path, "rb") as f:
        poller = client.begin_analyze_document("prebuilt-layout", body=f)
    result: AnalyzeResult = poller.result()

    print(f"Số trang: {len(result.pages)}")

    # Đọc bảng: số dòng/cột + nội dung từng ô
    if result.tables:
        for i, table in enumerate(result.tables):
            print(f"\nBảng {i}: {table.row_count} dòng x {table.column_count} cột")
            for cell in table.cells:
                print(f"  [{cell.row_index}][{cell.column_index}] = {cell.content!r}")
    else:
        print("Không có bảng nào.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
