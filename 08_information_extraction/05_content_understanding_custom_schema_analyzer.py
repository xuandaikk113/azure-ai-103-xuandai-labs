"""
====================================================================
LAB 08/05 · Content Understanding: Custom analyzer (schema tự định nghĩa)
--------------------------------------------------------------------
Dịch vụ      : Azure AI Content Understanding
Biến .env    : CONTENT_UNDERSTANDING_ENDPOINT, CONTENT_UNDERSTANDING_API_KEY
SDK tiền nhiệm: REST thủ công bằng requests -> azure-ai-contentunderstanding.
Chạy         : uv run 08_information_extraction/05_content_understanding_custom_schema_analyzer.py
⚠ Lưu ý      : README SDK chưa show code tạo custom analyzer. Khung dưới theo luồng chuẩn
               (create analyzer với field schema -> analyze -> delete). Đối chiếu sample
               "Analyzer Management" (tag azure-ai-contentunderstanding_1.1.0) cho tên model chính xác.
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

SAMPLE_DOC_URL = "https://<your-blob>/documents/contract.pdf"
CUSTOM_ANALYZER_ID = "ai103-contract-analyzer"


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
    # ── Alternative KEYLESS (Entra ID, khuyến nghị production) — thay cho AzureKeyCredential ──
    #   from azure.identity import DefaultAzureCredential
    #   client = ContentUnderstandingClient(
    #       endpoint=cfg["CONTENT_UNDERSTANDING_ENDPOINT"],
    #       credential=DefaultAzureCredential(),
    #   )
    #   (keyless chạy được khi principal có đúng RBAC data-plane role cho service này —
    #    vd Cognitive Services User trên resource Content Understanding; xem lab 00/04)

    # 1) Định nghĩa schema tuỳ chỉnh: mỗi field khai 'kind'
    #    - extract : rút thông tin có sẵn trong tài liệu
    #    - generate: để model SINH ra (vd tóm tắt)
    #    - classify: phân loại vào 1 nhóm
    analyzer_definition = {
        "description": "Trích thông tin hợp đồng",
        "fieldSchema": {
            "fields": {
                "PartyName": {"type": "string", "method": "extract"},
                "EffectiveDate": {"type": "date", "method": "extract"},
                "Summary": {"type": "string", "method": "generate"},
                "RiskLevel": {"type": "string", "method": "classify",
                              "enum": ["low", "medium", "high"]},
            }
        },
    }

    # 2) Tạo custom analyzer (long-running). Tên tham số/model theo sample Analyzer Management.
    client.begin_create_analyzer(
        analyzer_id=CUSTOM_ANALYZER_ID,
        analyzer=analyzer_definition,
    ).result()
    print(f"Đã tạo analyzer: {CUSTOM_ANALYZER_ID}")

    try:
        # 3) Phân tích tài liệu thật bằng analyzer vừa tạo
        poller = client.begin_analyze(
            analyzer_id=CUSTOM_ANALYZER_ID,
            inputs=[AnalysisInput(url=SAMPLE_DOC_URL)],
        )
        result: AnalysisResult = poller.result()
        fields = result.contents[0].fields or {}
        for name, field in fields.items():
            print(f"  {name}: {field.value if field else None}")
    finally:
        # 4) Dọn dẹp analyzer test
        client.delete_analyzer(analyzer_id=CUSTOM_ANALYZER_ID)
        print("Đã xoá analyzer test.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
