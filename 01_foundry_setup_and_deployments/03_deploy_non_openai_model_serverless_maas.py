"""
====================================================================
LAB 01/03 · Gọi model NON-OpenAI (Llama/Mistral/DeepSeek/Cohere) qua OpenAI /v1
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry Models (Serverless API / MaaS)
Biến .env    : FOUNDRY_MODELS_ENDPOINT (dạng .../openai/v1/), FOUNDRY_MODELS_API_KEY, FOUNDRY_NON_OPENAI_MODEL
SDK tiền nhiệm: azure-ai-inference (ChatCompletionsClient) ĐÃ DEPRECATED/retire 2026-08-26 -> nay dùng openai SDK /v1.
Chạy         : uv run 01_foundry_setup_and_deployments/03_deploy_non_openai_model_serverless_maas.py
Ghi chú      : phần "deploy" serverless làm trên portal/mgmt; file này tập trung GỌI model.
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
# openai (lớp OpenAI thuần, KHÔNG phải AzureOpenAI): trỏ base_url tới endpoint OpenAI /v1 của Foundry.
# Cùng một API này phục vụ cả model OpenAI lẫn non-OpenAI trong catalog Foundry.
from openai import OpenAI


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
    cfg = require_env("FOUNDRY_MODELS_ENDPOINT", "FOUNDRY_MODELS_API_KEY", "FOUNDRY_NON_OPENAI_MODEL")

    # Client OpenAI trỏ về endpoint /v1 của Foundry.
    # Keyless thay thế: lấy token Entra ID (scope https://ai.azure.com/.default) rồi truyền vào api_key.
    client = OpenAI(
        base_url=cfg["FOUNDRY_MODELS_ENDPOINT"],   # ví dụ: https://<res>.openai.azure.com/openai/v1/
        api_key=cfg["FOUNDRY_MODELS_API_KEY"],
    )

    # Gọi chat completion với model non-OpenAI (vd mistral-large-4-latest; tên catalog đổi theo thời gian)
    print(f"Hỏi model: {cfg['FOUNDRY_NON_OPENAI_MODEL']}")
    resp = client.chat.completions.create(
        model=cfg["FOUNDRY_NON_OPENAI_MODEL"],
        messages=[
            {"role": "system", "content": "Bạn là trợ lý trả lời ngắn gọn bằng tiếng Việt."},
            {"role": "user", "content": "Nêu 1 ưu điểm của serverless API (MaaS)."},
        ],
    )
    print("Trả lời:", resp.choices[0].message.content)
    # usage: số token tiêu thụ (để ước lượng chi phí)
    if resp.usage:
        print(f"Token: prompt={resp.usage.prompt_tokens}, completion={resp.usage.completion_tokens}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
