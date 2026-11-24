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

# ════════════════════════════════════════════════════════════════
# THAM CHIẾU — các loại credential trong azure-identity & KHI NÀO DÙNG
# ----------------------------------------------------------------
# DefaultAzureCredential KHÔNG phải 1 cách xác thực riêng — nó là 1 CHUỖI thử
# lần lượt nhiều credential, dùng cái đầu tiên có sẵn. Thứ tự (rút gọn):
#   1. EnvironmentCredential      -> đọc biến môi trường (AZURE_CLIENT_ID/TENANT_ID/CLIENT_SECRET...)
#   2. WorkloadIdentityCredential -> pod trên AKS (federated token, không secret)
#   3. ManagedIdentityCredential  -> MI của App Service/VM/Function/Container (PRODUCTION)
#   4. SharedTokenCacheCredential -> cache đăng nhập dùng chung (Windows)
#   5. VisualStudioCodeCredential -> danh tính đăng nhập trong VS Code
#   6. AzureCliCredential         -> danh tính bạn đã `az login` (DEV trên máy local)
#   7. AzurePowerShellCredential  -> `Connect-AzAccount` (PowerShell)
#   8. AzureDeveloperCliCredential-> danh tính `azd auth login`
#   (sau đó: InteractiveBrowser/Broker — mặc định TẮT; bật bằng tham số nếu cần)
#   => Nhờ vậy CÙNG 1 code chạy được cả local (CLI) lẫn production (Managed Identity)
#      mà không đổi dòng nào. Đây là lý do nên mặc định dùng DefaultAzureCredential.
#
# Khi cần CHỈ ĐỊNH RÕ 1 cách (nhanh hơn, khỏi dò cả chuỗi), import trực tiếp:
#
#   from azure.identity import AzureCliCredential
#   cred = AzureCliCredential()           # DEV local: dùng luôn `az login`, không dò lòng vòng
#
#   from azure.identity import ManagedIdentityCredential
#   cred = ManagedIdentityCredential()    # PROD: app chạy trên Azure có MI (xem lab 00/04)
#   # user-assigned MI: ManagedIdentityCredential(client_id="<client-id-cua-MI>")
#
#   from azure.identity import ClientSecretCredential
#   cred = ClientSecretCredential(tenant_id, client_id, client_secret)
#   # Service Principal có secret: CI/CD, job ngoài Azure. Có secret -> kém MI, cân nhắc.
#
#   from azure.identity import ClientCertificateCredential   # SP dùng cert thay secret (an toàn hơn secret)
#   from azure.identity import InteractiveBrowserCredential  # mở browser cho user đăng nhập (app desktop)
#   from azure.identity import DeviceCodeCredential          # nhập code trên thiết bị khác (máy không có browser)
#
# Tự dựng chuỗi ưu tiên riêng (vd chỉ CLI rồi MI) bằng ChainedTokenCredential:
#   from azure.identity import ChainedTokenCredential, AzureCliCredential, ManagedIdentityCredential
#   cred = ChainedTokenCredential(AzureCliCredential(), ManagedIdentityCredential())
#
# BẢNG CHỌN NHANH:
#   | Tình huống                          | Nên dùng                                  |
#   |-------------------------------------|-------------------------------------------|
#   | Dev trên máy local                  | DefaultAzureCredential (qua AzureCli)     |
#   | App chạy trên Azure (App Svc/VM/AKS)| ManagedIdentityCredential / DefaultAzure… |
#   | CI/CD pipeline                      | OIDC/WorkloadIdentity, hoặc ClientSecret  |
#   | App desktop có user tương tác       | InteractiveBrowserCredential              |
#   | Máy/thiết bị không có trình duyệt   | DeviceCodeCredential                      |
#   | Nhiều môi trường, 1 codebase        | DefaultAzureCredential (mặc định)         |
# async: dùng bản trong `azure.identity.aio` (cùng tên class) cho code bất đồng bộ.
# ════════════════════════════════════════════════════════════════

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
