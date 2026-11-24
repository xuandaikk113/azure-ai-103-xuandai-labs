"""
====================================================================
LAB 01/01 · Auth: API key vs DefaultAzureCredential (keyless)
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI (qua openai SDK)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT
SDK tiền nhiệm: trước đây hay hard-code API key / dùng azure-common.
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
# azure-identity: keyless. get_bearer_token_provider bọc credential thành hàm trả token
# đúng chuẩn mà openai SDK cần (azure_ad_token_provider).
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# ── SDK Azure OpenAI ────────────────────────────────────────────
# openai>=1.x: lớp AzureOpenAI. (Tiền nhiệm: openai<1.0 dùng openai.ChatCompletion.create.)
from openai import AzureOpenAI


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def ask_model(client: AzureOpenAI, deployment: str, method: str) -> None:
    """Gửi 1 câu hỏi ngắn để chứng minh client hoạt động."""
    resp = client.chat.completions.create(
        model=deployment,       # LƯU Ý: 'model' = tên DEPLOYMENT, không phải tên model gốc
        messages=[{"role": "user", "content": "Trả lời đúng 1 từ: Azure"}],
        max_tokens=5,
    )
    print(f"[{method}] -> {resp.choices[0].message.content!r}")


def main() -> None:
    cfg = require_env(
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_CHAT_DEPLOYMENT",
    )
    endpoint = cfg["AZURE_OPENAI_ENDPOINT"]
    api_version = cfg["AZURE_OPENAI_API_VERSION"]
    deployment = cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    # ── CÁCH 1: API key (đơn giản nhưng key là bí mật, dễ lộ) ──
    client_key = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=cfg["AZURE_OPENAI_API_KEY"],
        api_version=api_version,
    )
    ask_model(client_key, deployment, "api_key")

    # ── CÁCH 2: keyless (DefaultAzureCredential) — BEST PRACTICE ──
    # Bật log để thấy nó thử EnvironmentCredential -> ManagedIdentity -> AzureCli ...
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("azure.identity").setLevel(logging.INFO)

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",   # scope token của Azure OpenAI
    )
    client_keyless = AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,           # thay cho api_key
        api_version=api_version,
    )
    ask_model(client_keyless, deployment, "keyless")

    print("\nKết luận: ưu tiên keyless (Entra ID) — không secret, cấp quyền qua RBAC.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
