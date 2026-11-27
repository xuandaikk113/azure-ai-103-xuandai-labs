"""
====================================================================
LAB 08/02 · Document Intelligence: prebuilt-invoice + prebuilt-idDocument
--------------------------------------------------------------------
Dịch vụ      : Azure AI Document Intelligence
Biến .env    : DOC_INTELLIGENCE_ENDPOINT, DOC_INTELLIGENCE_API_KEY
SDK tiền nhiệm: Form Recognizer -> azure-ai-documentintelligence.
Chạy         : uv run 08_information_extraction/02_doc_intelligence_prebuilt_invoice_and_id.py
Cần          : assets/sample_invoice.pdf (và tuỳ chọn assets/sample_id.jpg)
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


def analyze_prebuilt(client: DocumentIntelligenceClient, model_id: str, path: str, field_names: list) -> None:
    """Chạy 1 prebuilt model và in các field + độ tin cậy (confidence)."""
    with open(path, "rb") as f:
        poller = client.begin_analyze_document(model_id, body=f)
    result: AnalyzeResult = poller.result()

    for doc in result.documents or []:
        fields = doc.fields or {}
        for name in field_names:
            field = fields.get(name)
            if field:
                # field.get('valueString') lấy giá trị chuẩn hoá; .confidence là độ tin cậy
                print(f"  {name}: {field.get('valueString')} (conf={field.confidence})")


def main() -> None:
    cfg = require_env("DOC_INTELLIGENCE_ENDPOINT", "DOC_INTELLIGENCE_API_KEY")
    client = DocumentIntelligenceClient(
        cfg["DOC_INTELLIGENCE_ENDPOINT"], AzureKeyCredential(cfg["DOC_INTELLIGENCE_API_KEY"]),
    )
    # ── Alternative KEYLESS (Entra ID, khuyến nghị production) — thay cho AzureKeyCredential ──
    #   from azure.identity import DefaultAzureCredential
    #   client = DocumentIntelligenceClient(cfg["DOC_INTELLIGENCE_ENDPOINT"], DefaultAzureCredential())
    #   (keyless chạy được khi principal có đúng RBAC data-plane role cho service này —
    #    vd Cognitive Services User trên resource Document Intelligence; xem lab 00/04)

    # 1) Hoá đơn
    invoice_path = os.path.join("assets", "sample_invoice.pdf")
    if os.path.exists(invoice_path):
        print("== Invoice ==")
        analyze_prebuilt(client, "prebuilt-invoice", invoice_path,
                         ["VendorName", "InvoiceId", "InvoiceTotal", "InvoiceDate"])
    else:
        print(f"(bỏ qua invoice: chưa có {invoice_path})")

    # 2) Giấy tờ tuỳ thân
    id_path = os.path.join("assets", "sample_id.jpg")
    if os.path.exists(id_path):
        print("\n== ID Document ==")
        analyze_prebuilt(client, "prebuilt-idDocument", id_path,
                         ["FirstName", "LastName", "DocumentNumber", "DateOfBirth"])
    else:
        print(f"(bỏ qua ID: chưa có {id_path})")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
