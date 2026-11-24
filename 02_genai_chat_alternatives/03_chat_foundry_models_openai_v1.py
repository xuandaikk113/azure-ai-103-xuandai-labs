"""
====================================================================
LAB 02/03 · Foundry Models qua OpenAI /v1 (chat + embeddings)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry Models (endpoint OpenAI /v1)
Biến .env    : FOUNDRY_MODELS_ENDPOINT (.../openai/v1/), FOUNDRY_MODELS_API_KEY,
               FOUNDRY_NON_OPENAI_MODEL, AZURE_OPENAI_EMBEDDING_DEPLOYMENT
SDK tiền nhiệm: azure-ai-inference (ChatCompletionsClient/EmbeddingsClient) ĐÃ DEPRECATED -> openai /v1.
Chạy         : uv run 02_genai_chat_alternatives/03_chat_foundry_models_openai_v1.py
Khác lab 01  : đây là endpoint Foundry Models (catalog), không phải Azure OpenAI thuần.
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

# ── SDK ─────────────────────────────────────────────────────────
from openai import OpenAI       # OpenAI thuần + base_url của Foundry; 1 API cho cả chat lẫn embeddings


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
        "FOUNDRY_MODELS_ENDPOINT", "FOUNDRY_MODELS_API_KEY",
        "FOUNDRY_NON_OPENAI_MODEL", "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    )

    client = OpenAI(base_url=cfg["FOUNDRY_MODELS_ENDPOINT"], api_key=cfg["FOUNDRY_MODELS_API_KEY"])

    # 1) Chat với model trong catalog Foundry
    chat = client.chat.completions.create(
        model=cfg["FOUNDRY_NON_OPENAI_MODEL"],
        messages=[{"role": "user", "content": "Nói 'xin chào' bằng 3 ngôn ngữ."}],
    )
    print("Chat:", chat.choices[0].message.content)

    # 2) Embeddings: biến text thành vector (dùng cho RAG / tìm kiếm ngữ nghĩa)
    emb = client.embeddings.create(
        model=cfg["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
        input="Azure AI Search hỗ trợ vector search.",
    )
    vector = emb.data[0].embedding
    print(f"Embedding: {len(vector)} chiều, 3 giá trị đầu = {vector[:3]}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
