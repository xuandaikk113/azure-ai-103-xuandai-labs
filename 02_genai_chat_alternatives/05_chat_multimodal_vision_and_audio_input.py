"""
====================================================================
LAB 02/05 · Multimodal input (ảnh + text)
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI (model multimodal, vd gpt-4o)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT
SDK tiền nhiệm: không.
Chạy         : uv run 02_genai_chat_alternatives/05_chat_multimodal_vision_and_audio_input.py
Cần          : ảnh mẫu tại assets/sample_image.jpg
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import base64                   # mã hoá ảnh thành chuỗi base64 để nhúng vào message

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── SDK ─────────────────────────────────────────────────────────
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


def main() -> None:
    cfg = require_env(
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_CHAT_DEPLOYMENT",
    )
    client = AzureOpenAI(
        azure_endpoint=cfg["AZURE_OPENAI_ENDPOINT"],
        api_key=cfg["AZURE_OPENAI_API_KEY"],
        api_version=cfg["AZURE_OPENAI_API_VERSION"],
    )

    # Đọc ảnh -> base64 -> data URL
    image_path = os.path.join("assets", "sample_image.jpg")
    if not os.path.exists(image_path):
        sys.exit(f"[THIẾU DỮ LIỆU] Đặt ảnh tại: {image_path}")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    data_url = f"data:image/jpeg;base64,{b64}"

    # message content là danh sách 'part': vừa text vừa ảnh
    resp = client.chat.completions.create(
        model=cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"],
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Mô tả ngắn gọn ảnh này bằng tiếng Việt."},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
    )
    print("Mô tả ảnh:", resp.choices[0].message.content)

    # Lưu ý bảo mật: cảnh giác PROMPT INJECTION ẩn trong chữ của ảnh
    # (ảnh có thể chứa text ra lệnh cho model) -> đừng tin tuyệt đối nội dung từ ảnh.
    print("\nLưu ý: text nằm trong ảnh có thể là prompt injection — không tin tuyệt đối.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
