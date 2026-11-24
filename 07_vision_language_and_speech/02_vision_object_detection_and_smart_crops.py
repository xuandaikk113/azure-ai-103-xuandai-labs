"""
====================================================================
LAB 07/02 · Image Analysis: Objects, People, Smart Crops
--------------------------------------------------------------------
Dịch vụ      : Azure AI Vision - Image Analysis 4.0
Biến .env    : VISION_ENDPOINT, VISION_API_KEY
SDK tiền nhiệm: Computer Vision 3.x -> azure-ai-vision-imageanalysis.
Chạy         : uv run 07_vision_language_and_speech/02_vision_object_detection_and_smart_crops.py
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
from azure.ai.vision.imageanalysis.models import VisualFeatures


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
    with open(image_path, "rb") as f:
        image_data = f.read()

    result = client.analyze(
        image_data=image_data,
        visual_features=[
            VisualFeatures.OBJECTS,      # phát hiện vật thể + bounding box
            VisualFeatures.PEOPLE,       # phát hiện người
            VisualFeatures.SMART_CROPS,  # gợi ý vùng cắt ảnh thông minh
        ],
        smart_crops_aspect_ratios=[1.0, 1.78],   # yêu cầu crop theo tỉ lệ 1:1 và 16:9
    )

    if result.objects:
        print("Objects:")
        for obj in result.objects.list:
            box = obj.bounding_box
            print(f"  - {obj.tags[0].name} tại (x={box.x}, y={box.y}, w={box.width}, h={box.height})")
    if result.people:
        print(f"Số người phát hiện: {len(result.people.list)}")
    if result.smart_crops:
        for crop in result.smart_crops.list:
            print(f"Smart crop tỉ lệ {crop.aspect_ratio}: {crop.bounding_box}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
