"""
====================================================================
LAB 01/04 · Inspect Foundry project: connections & deployments
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry project
Biến .env    : FOUNDRY_PROJECT_ENDPOINT
SDK tiền nhiệm: azure-ai-resources / thao tác portal.
Chạy         : uv run 01_foundry_setup_and_deployments/04_inspect_foundry_project_and_connections.py
Lưu ý        : AIProjectClient CHỈ hỗ trợ xác thực Entra ID (không dùng API key).
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

# ── xác thực keyless (bắt buộc với AIProjectClient) ─────────────
from azure.identity import DefaultAzureCredential

# ── SDK Foundry project ─────────────────────────────────────────
# azure-ai-projects (2.x): AIProjectClient là cửa ngõ vào project.
# Gói azure-ai-agents cũ đã GỘP vào đây (agent qua project_client.agents.*).
from azure.ai.projects import AIProjectClient


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
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT")

    # Khởi tạo client project (endpoint + credential Entra ID)
    project = AIProjectClient(
        endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
    )

    # 1) Liệt kê các connection (AI Search, Storage, Key Vault, model provider...)
    print("== Connections ==")
    for conn in project.connections.list():
        # mỗi connection có name + type (loại tài nguyên được kết nối)
        print(f"  - {conn.name}  (type={getattr(conn, 'type', '?')})")

    # 2) Liệt kê deployments (các model đã deploy trong project)
    #    Bọc try/except vì bề mặt API có thể khác giữa các bản SDK.
    print("\n== Deployments ==")
    try:
        for dep in project.deployments.list():
            print(f"  - {dep.name}")
    except Exception as e:
        print(f"  (không liệt kê được deployments: {type(e).__name__} - tra Microsoft Learn nếu API đổi)")

    # 3) Lấy OpenAI client gắn với project để gọi model (minh hoạ)
    #    get_openai_client() trả về client openai đã cấu hình sẵn endpoint/auth của project.
    print("\nMẹo: project.get_openai_client() cho ra client openai để gọi model/Responses ngay.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
