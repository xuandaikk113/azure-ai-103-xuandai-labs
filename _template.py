"""
====================================================================
LAB <NN> · <Tên lab> — <mục tiêu 1 dòng>
--------------------------------------------------------------------
Dịch vụ Azure/Foundry : <...>
Biến .env cần         : <LIST biến>
SDK tiền nhiệm        : <vd: Form Recognizer -> Document Intelligence; hoặc "không có">
Chạy                  : uv run <đường_dẫn_file>.py
====================================================================
File MẪU (template). Copy sang lab mới rồi điền phần TODO.
Mọi file lab phải là STANDALONE và CHẠY ĐƯỢC (theo AGENTS.md).
"""

# ── stdlib ──────────────────────────────────────────────────────
import os                       # đọc biến môi trường
import sys                      # thoát chương trình khi thiếu cấu hình

# Windows: console mặc định cp1252 không in được tiếng Việt -> ép stdout sang UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
# python-dotenv: nạp file .env vào os.environ (không phải SDK Azure, chỉ tiện cho local dev).
from dotenv import load_dotenv

# ── xác thực Azure (keyless / Entra ID) ─────────────────────────
# azure-identity: DefaultAzureCredential tự thử chuỗi credential
# EnvironmentCredential -> ManagedIdentity -> AzureCliCredential ...
# (Tiền nhiệm: trước đây hay hard-code API key — nay ưu tiên keyless.)
from azure.identity import DefaultAzureCredential

# ── SDK riêng của lab này ───────────────────────────────────────
# TODO: import SDK cụ thể, mỗi dòng 1 comment giải thích + nhắc SDK tiền nhiệm nếu có.
# Ví dụ:
#   from openai import AzureOpenAI   # thay cho openai<1.0 (openai.ChatCompletion.create)


def require_env(*names: str) -> dict:
    """Nạp .env rồi đọc các biến BẮT BUỘC; thiếu biến nào thì báo rõ và thoát."""
    load_dotenv()                                 # tìm .env ở thư mục hiện tại trở lên
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


def main() -> None:
    # 1) Đọc cấu hình bắt buộc (đổi tên biến theo lab)
    cfg = require_env("AZURE_OPENAI_ENDPOINT")

    # 2) Khởi tạo client — ưu tiên keyless; nêu cả cách dùng API key trong comment
    credential = DefaultAzureCredential()
    # TODO: tạo client dịch vụ, truyền endpoint (cfg[...]) + credential

    # 3) Logic chính của lab
    # TODO

    # 4) In kết quả dễ đọc
    print("TODO: in kết quả của lab")


if __name__ == "__main__":
    # Bắt lỗi để khi học thấy thông báo thân thiện thay vì traceback dài.
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
