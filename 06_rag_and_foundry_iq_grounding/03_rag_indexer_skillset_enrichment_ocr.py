"""
====================================================================
LAB 06/03 · Ingestion pipeline: Data source -> Skillset (OCR+Split) -> Indexer
--------------------------------------------------------------------
Dịch vụ      : Azure AI Search (indexer + skillset)
Biến .env    : AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, AZURE_SEARCH_INDEX, BLOB_CONNECTION_STRING
SDK tiền nhiệm: Azure Cognitive Search -> Azure AI Search.
Chạy         : uv run 06_rag_and_foundry_iq_grounding/03_rag_indexer_skillset_enrichment_ocr.py
Ghi chú      : tạo luồng ingest tự động từ blob 'documents' -> index. Chạy 1 lần để dựng pipeline.
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

# ── SDK (management plane của Search: tạo index/indexer/skillset) ─
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType,
    SearchIndexerDataSourceConnection, SearchIndexerDataContainer,
    SearchIndexerSkillset, OcrSkill, SplitSkill,
    InputFieldMappingEntry, OutputFieldMappingEntry,
    SearchIndexer, FieldMapping,
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
    cfg = require_env(
        "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX", "BLOB_CONNECTION_STRING",
    )
    endpoint = cfg["AZURE_SEARCH_ENDPOINT"]
    credential = AzureKeyCredential(cfg["AZURE_SEARCH_API_KEY"])
    index_name = cfg["AZURE_SEARCH_INDEX"]
    # ── Alternative KEYLESS (Entra ID, khuyến nghị production) — thay cho AzureKeyCredential ──
    #   from azure.identity import DefaultAzureCredential
    #   credential = DefaultAzureCredential()
    #   index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
    #   indexer_client = SearchIndexerClient(endpoint=endpoint, credential=credential)
    #   (keyless chạy được khi principal có đúng RBAC data-plane role cho Search —
    #    tạo index/indexer/skillset cần Search Index Data Contributor / Search Service Contributor; xem lab 00/04)

    # 1) INDEX đích: nơi chứa dữ liệu sau khi enrich
    index_client = SearchIndexClient(endpoint, credential)
    index_client.create_or_update_index(SearchIndex(
        name=index_name,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
        ],
    ))
    print(f"Index '{index_name}' sẵn sàng.")

    indexer_client = SearchIndexerClient(endpoint, credential)

    # 2) DATA SOURCE: trỏ tới container blob 'documents'
    indexer_client.create_or_update_data_source_connection(
        SearchIndexerDataSourceConnection(
            name="ai103-datasource",
            type="azureblob",
            connection_string=cfg["BLOB_CONNECTION_STRING"],
            container=SearchIndexerDataContainer(name="documents"),
        )
    )

    # 3) SKILLSET: enrich = OCR (ảnh/scan -> text) rồi Split (chia nhỏ chunk)
    ocr = OcrSkill(
        inputs=[InputFieldMappingEntry(name="image", source="/document/normalized_images/*")],
        outputs=[OutputFieldMappingEntry(name="text", target_name="ocrText")],
    )
    split = SplitSkill(
        text_split_mode="pages", maximum_page_length=2000,
        inputs=[InputFieldMappingEntry(name="text", source="/document/content")],
        outputs=[OutputFieldMappingEntry(name="textItems", target_name="chunks")],
    )
    indexer_client.create_or_update_skillset(SearchIndexerSkillset(
        name="ai103-skillset", skills=[ocr, split], description="OCR + chunking",
    ))

    # 4) INDEXER: nối data source + skillset -> đẩy vào index
    indexer_client.create_or_update_indexer(SearchIndexer(
        name="ai103-indexer",
        data_source_name="ai103-datasource",
        target_index_name=index_name,
        skillset_name="ai103-skillset",
        field_mappings=[FieldMapping(source_field_name="metadata_storage_path", target_field_name="id")],
    ))
    print("Đã tạo indexer. Search sẽ tự động ingest dữ liệu từ blob.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
