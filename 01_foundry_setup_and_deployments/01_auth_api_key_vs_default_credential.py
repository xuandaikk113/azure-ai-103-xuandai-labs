"""
====================================================================
LAB 01/01 · Auth: API key vs DefaultAzureCredential (keyless) — qua OpenAI /v1
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI (endpoint /v1, qua openai SDK)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT
SDK tiền nhiệm: hard-code API key / AzureOpenAI(api_version=...) -> nay dùng OpenAI /v1.
Chạy         : uv run 01_foundry_setup_and_deployments/01_auth_api_key_vs_default_credential.py
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import logging                  # để xem chuỗi credential DefaultAzureCredential thử lần lượt

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── xác thực ────────────────────────────────────────────────────
# azure-identity: keyless. get_bearer_token_provider trả 1 hàm token -> truyền thẳng vào
# api_key của OpenAI client để TỰ ĐỘNG lấy & làm mới token (không cần secret tĩnh).
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# ── SDK Azure OpenAI ────────────────────────────────────────────
# openai (lớp OpenAI thuần) + base_url /openai/v1/ là cách KHUYẾN NGHỊ (không cần api_version).
# (Tiền nhiệm: AzureOpenAI(azure_endpoint=..., api_version=...) — vẫn chạy nhưng không còn ưu tiên.)
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


def ask_model(client: OpenAI, deployment: str, method: str) -> None:
    """Gửi 1 câu hỏi ngắn để chứng minh client hoạt động."""
    resp = client.responses.create(
        model=deployment,          # 'model' = tên DEPLOYMENT
        input="Trả lời đúng 1 từ: Azure",
    )
    print(f"[{method}] -> {resp.output_text!r}")


def main() -> None:
    cfg = require_env("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_CHAT_DEPLOYMENT")
    base_url = cfg["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1/"
    deployment = cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    # ── CÁCH 1: API key (đơn giản nhưng key là bí mật, dễ lộ) ──
    client_key = OpenAI(base_url=base_url, api_key=cfg["AZURE_OPENAI_API_KEY"])
    ask_model(client_key, deployment, "api_key")

    # ── CÁCH 2: keyless (Entra ID) — BEST PRACTICE ──
    # Bật log để thấy nó thử EnvironmentCredential -> ManagedIdentity -> AzureCli ...
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("azure.identity").setLevel(logging.INFO)

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://ai.azure.com/.default",   # scope token cho OpenAI /v1 (khác scope của Inference SDK cũ)
    )
    # Truyền token_provider vào api_key -> openai SDK tự lấy/làm mới token.
    client_keyless = OpenAI(base_url=base_url, api_key=token_provider)
    ask_model(client_keyless, deployment, "keyless")

    print("\nKết luận: ưu tiên keyless (Entra ID) — không secret, cấp quyền qua RBAC.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
