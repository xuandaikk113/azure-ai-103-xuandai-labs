"""
====================================================================
LAB 02/05 · Multimodal input (ảnh + text)
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI (model multimodal, vd gpt-4o)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT (v1: bỏ api_version)
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
    # Alternative KEYLESS (khuyến nghị production) — không cần API key, dùng Entra ID:
    #   from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    #   token_provider = get_bearer_token_provider(
    #       DefaultAzureCredential(), "https://ai.azure.com/.default")   # scope token cho /openai/v1
    #   client = OpenAI(base_url=..., api_key=token_provider)            # truyền token provider vào api_key

    # Đọc ảnh -> base64 -> data URL
    image_path = os.path.join("assets", "sample_image.jpg")
    if not os.path.exists(image_path):
        sys.exit(f"[THIẾU DỮ LIỆU] Đặt ảnh tại: {image_path}")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    data_url = f"data:image/jpeg;base64,{b64}"

    deployment = cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"]

    # ─────────────────────────────────────────────────────────────
    # CÁCH 1 · chat.completions + ảnh dạng BASE64 (data URL)
    # message content là danh sách 'part': vừa text vừa ảnh.
    # Dùng base64 khi ảnh nằm ở máy/local, KHÔNG có URL công khai.
    # ─────────────────────────────────────────────────────────────
    chat_response = client.chat.completions.create(
        model=deployment,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Mô tả ngắn gọn ảnh này bằng tiếng Việt."},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
    )
    print("[base64 + chat.completions] Mô tả ảnh:", chat_response.choices[0].message.content)

    # ─────────────────────────────────────────────────────────────
    # CÁCH 2 · ảnh dạng IMAGE URL công khai (không cần base64)
    # Khi ảnh đã có URL công khai (vd trên Blob/CDN) thì truyền THẲNG url,
    # nhẹ hơn nhiều so với nhúng cả base64 vào request.
    # ─────────────────────────────────────────────────────────────
    public_image_url = (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/"
        "Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-"
        "Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
    )  # đổi thành URL ảnh công khai bất kỳ
    chat_response_from_url = client.chat.completions.create(
        model=deployment,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Trong ảnh có gì?"},
                # chỉ khác CÁCH 1 ở chỗ 'url' là http URL thật, không phải data URL base64
                {"type": "image_url", "image_url": {"url": public_image_url}},
            ],
        }],
    )
    print("[image url + chat.completions] Mô tả ảnh:", chat_response_from_url.choices[0].message.content)

    # ─────────────────────────────────────────────────────────────
    # CÁCH 3 · Responses API (chuẩn mới) — cùng input ảnh nhưng CÚ PHÁP KHÁC
    #   chat.completions: part {"type": "image_url", "image_url": {"url": ...}}
    #   responses       : part {"type": "input_image", "image_url": "<url hoặc data url>"}
    # ─────────────────────────────────────────────────────────────
    image_response = client.responses.create(
        model=deployment,
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Mô tả ngắn gọn ảnh này bằng tiếng Việt."},
                {"type": "input_image", "image_url": public_image_url},   # hoặc dùng lại data_url base64
            ],
        }],
    )
    print("[image url + responses]       Mô tả ảnh:", image_response.output_text)

    # Lưu ý bảo mật: cảnh giác PROMPT INJECTION ẩn trong chữ của ảnh
    # (ảnh có thể chứa text ra lệnh cho model) -> đừng tin tuyệt đối nội dung từ ảnh.
    print("\nLưu ý: text nằm trong ảnh có thể là prompt injection — không tin tuyệt đối.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
