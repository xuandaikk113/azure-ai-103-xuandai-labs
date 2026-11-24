"""
====================================================================
LAB 02/04 · Streaming + Structured output (JSON Schema strict)
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT (v1: bỏ api_version)
SDK tiền nhiệm: không (dùng openai SDK hiện hành).
Chạy         : uv run 02_genai_chat_alternatives/04_chat_streaming_and_structured_json_schema.py
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import json                     # parse chuỗi JSON model trả về

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── SDK ─────────────────────────────────────────────────────────
from openai import OpenAI   # client trỏ endpoint Azure OpenAI /v1 (cách khuyến nghị)


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
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_CHAT_DEPLOYMENT",
    )
    # Cách KHUYẾN NGHỊ (v1): base_url trỏ /openai/v1/, KHÔNG cần api_version.
    client = OpenAI(
        base_url=cfg["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1/",
        api_key=cfg["AZURE_OPENAI_API_KEY"],
    )
    # Alternative CLASSIC (vẫn hỗ trợ, chưa deprecated) - xem file 02/01:
    #   from openai import AzureOpenAI
    #   client = AzureOpenAI(azure_endpoint=cfg["AZURE_OPENAI_ENDPOINT"],
    #                        api_key=cfg["AZURE_OPENAI_API_KEY"], api_version="2025-04-01-preview")
    deployment = cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    # ── 1) STREAMING: nhận từng mảnh (delta) theo thời gian thực ──
    print("Streaming: ", end="", flush=True)
    stream = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": "Đếm từ 1 đến 5."}],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()

    # ── 2) STRUCTURED OUTPUT: ép model trả JSON đúng schema (strict) ──
    # strict=True + additionalProperties=False => model buộc tuân thủ schema.
    schema = {
        "type": "object",
        "properties": {
            "ten": {"type": "string"},
            "tuoi": {"type": "integer"},
            "so_thich": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["ten", "tuoi", "so_thich"],
        "additionalProperties": False,
    }
    resp = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": "Tạo 1 hồ sơ nhân vật giả tưởng."}],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "ho_so", "schema": schema, "strict": True},
        },
    )
    data = json.loads(resp.choices[0].message.content)   # chắc chắn parse được vì strict
    print("Structured:", data)
    print("Kiểu tuoi:", type(data["tuoi"]).__name__)      # int, không phải string


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
