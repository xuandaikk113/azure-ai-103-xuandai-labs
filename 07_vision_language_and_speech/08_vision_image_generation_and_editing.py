"""
====================================================================
LAB 07/08 · Image generation + editing (text-to-image, inpainting)
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI (model image, vd gpt-image-1)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_IMAGE_DEPLOYMENT (v1: bỏ api_version)
SDK tiền nhiệm: không.
Lưu ý        : tạo ảnh/video đôi khi cần api-version preview -> nếu v1 GA chưa hỗ trợ, dùng AzureOpenAI (comment).
Chạy         : uv run 07_vision_language_and_speech/08_vision_image_generation_and_editing.py
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import base64                   # ảnh trả về dạng base64 -> giải mã để lưu file

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── SDK ─────────────────────────────────────────────────────────
from openai import OpenAI   # client v1 (khuyến nghị)

OUTPUT_DIR = os.path.join("assets", "output")


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
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_IMAGE_DEPLOYMENT",
    )
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Cách KHUYẾN NGHỊ (v1). Nếu model image chưa có trong v1 GA, dùng AzureOpenAI + api_version preview.
    client = OpenAI(
        base_url=cfg["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1/",
        api_key=cfg["AZURE_OPENAI_API_KEY"],
    )
    deployment = cfg["AZURE_OPENAI_IMAGE_DEPLOYMENT"]

    # 1) TEXT-TO-IMAGE: tạo ảnh từ mô tả
    result = client.images.generate(
        model=deployment,
        prompt="Một chú mèo phi hành gia dễ thương, phong cách hoạt hình",
        size="1024x1024",        # generation control: kích thước
        n=1,
    )
    out_path = os.path.join(OUTPUT_DIR, "generated.png")
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(result.data[0].b64_json))
    print("Đã tạo ảnh:", out_path)

    # 2) EDITING (inpainting): sửa vùng theo mask + prompt
    #    Cần ảnh gốc + mask (vùng trong suốt = vùng được vẽ lại).
    base_img = os.path.join("assets", "sample_image.png")
    mask_img = os.path.join("assets", "sample_mask.png")
    if os.path.exists(base_img) and os.path.exists(mask_img):
        edited = client.images.edit(
            model=deployment,
            image=open(base_img, "rb"),
            mask=open(mask_img, "rb"),
            prompt="Thêm một chiếc mũ đỏ vào vùng được chọn",
        )
        edit_path = os.path.join(OUTPUT_DIR, "edited.png")
        with open(edit_path, "wb") as f:
            f.write(base64.b64decode(edited.data[0].b64_json))
        print("Đã sửa ảnh:", edit_path)
    else:
        print("(bỏ qua inpainting: cần assets/sample_image.png + assets/sample_mask.png)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
