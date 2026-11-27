"""Cấu hình tập trung cho trợ lý (đọc từ biến môi trường / .env).

Mọi module khác lấy cấu hình qua get_settings() thay vì đọc os.environ rải rác —
dễ test (inject settings) và dễ đổi provider.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv   # nạp .env khi chạy local

load_dotenv()

# Thư mục gốc của module (…/10_production_assistant_agent): dùng cho đường dẫn data mặc định.
MODULE_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Toàn bộ cấu hình runtime. frozen=True để bất biến, tránh sửa nhầm lúc chạy."""

    # ── LLM provider: 'foundry' (mặc định) hoặc 'openai' (Azure OpenAI /v1) ──
    llm_provider: str = os.getenv("ASSISTANT_LLM_PROVIDER", "foundry")

    # Foundry (keyless qua DefaultAzureCredential)
    foundry_project_endpoint: str | None = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
    foundry_model: str = os.getenv("FOUNDRY_MODEL", "gpt-4o")

    # Azure OpenAI /v1 (khi llm_provider='openai')
    azure_openai_endpoint: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = os.getenv("AZURE_OPENAI_API_KEY")   # optional — bỏ nếu keyless
    azure_openai_chat_deployment: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")

    # ── Tài nguyên LOCAL/MOCK (chạy offline, không cần Azure thật) ──
    mock_api_base_url: str = os.getenv("MOCK_API_BASE_URL", "http://localhost:8000")
    sales_db_path: str = os.getenv("SALES_DB_PATH", str(MODULE_ROOT / "data" / "sales.sqlite"))
    internal_docs_dir: str = os.getenv("INTERNAL_DOCS_DIR", str(MODULE_ROOT / "data" / "internal_docs"))
    chart_output_dir: str = os.getenv("CHART_OUTPUT_DIR", str(MODULE_ROOT / "data" / "charts"))


def get_settings() -> Settings:
    """Trả về cấu hình hiện tại (đọc lại env mỗi lần gọi cho tiện test)."""
    return Settings()
