"""
====================================================================
LAB 07/01 · Image Analysis: Caption, Dense Captions, Tags, Read (OCR)
--------------------------------------------------------------------
Dịch vụ      : Azure AI Vision - Image Analysis 4.0
Biến .env    : VISION_ENDPOINT, VISION_API_KEY
SDK tiền nhiệm: azure-cognitiveservices-vision-computervision (Computer Vision 3.x) -> azure-ai-vision-imageanalysis.
Chạy         : uv run 07_vision_language_and_speech/01_vision_image_analysis_captions_tags_ocr.py
Cần          : ảnh mẫu assets/sample_image.jpg
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

# ── xác thực ────────────────────────────────────────────────────
from azure.core.credentials import AzureKeyCredential

# ── SDK Image Analysis ──────────────────────────────────────────
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures   # danh sách feature cần phân tích


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
    cfg = require_env("VISION_ENDPOINT", "VISION_API_KEY")
    image_path = os.path.join("assets", "sample_image.jpg")
    if not os.path.exists(image_path):
        sys.exit(f"[THIẾU DỮ LIỆU] Đặt ảnh tại: {image_path}")

    client = ImageAnalysisClient(cfg["VISION_ENDPOINT"], AzureKeyCredential(cfg["VISION_API_KEY"]))
    # ── Alternative KEYLESS (Entra ID, khuyến nghị production) — thay cho AzureKeyCredential ──
    #   from azure.identity import DefaultAzureCredential
    #   client = ImageAnalysisClient(cfg["VISION_ENDPOINT"], DefaultAzureCredential())
    #   (keyless chạy được khi principal có đúng RBAC data-plane role cho service này —
    #    vd Cognitive Services User trên resource Vision; xem lab 00/04)
    with open(image_path, "rb") as f:
        image_data = f.read()

    # 1 call -> nhiều feature cùng lúc (ưu điểm Image Analysis 4.0)
    result = client.analyze(
        image_data=image_data,
        visual_features=[
            VisualFeatures.CAPTION,         # mô tả tổng thể 1 câu
            VisualFeatures.DENSE_CAPTIONS,  # mô tả chi tiết từng vùng
            VisualFeatures.TAGS,            # nhãn nội dung
            VisualFeatures.READ,            # OCR đọc chữ trong ảnh
        ],
    )

    if result.caption:
        print(f"Caption: {result.caption.text} (conf={result.caption.confidence:.2f})")
    if result.tags:
        print("Tags:", [t.name for t in result.tags.list])
    if result.read:
        print("Text (OCR):")
        for block in result.read.blocks:
            for line in block.lines:
                print("  ", line.text)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
