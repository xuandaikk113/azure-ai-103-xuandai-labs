"""
====================================================================
LAB 08/04 · Content Understanding: Audio / Video (đa phương thức)
--------------------------------------------------------------------
Dịch vụ      : Azure AI Content Understanding
Biến .env    : CONTENT_UNDERSTANDING_ENDPOINT, CONTENT_UNDERSTANDING_API_KEY
SDK tiền nhiệm: REST thủ công bằng requests -> azure-ai-contentunderstanding.
Chạy         : uv run 08_information_extraction/04_content_understanding_audio_video_multimodal.py
Lưu ý        : điểm mạnh của CU là ĐA PHƯƠNG THỨC (document/audio/video/image) — khác Document
               Intelligence (chỉ document). Input qua URL.
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

# ── SDK Content Understanding ───────────────────────────────────
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import AnalysisInput, AnalysisResult

# Thay bằng URL file audio/video của bạn (blob + SAS)
SAMPLE_AUDIO_URL = "https://<your-blob>/media/sample.wav"
SAMPLE_VIDEO_URL = "https://<your-blob>/media/sample.mp4"


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
    cfg = require_env("CONTENT_UNDERSTANDING_ENDPOINT", "CONTENT_UNDERSTANDING_API_KEY")
    client = ContentUnderstandingClient(
        endpoint=cfg["CONTENT_UNDERSTANDING_ENDPOINT"],
        credential=AzureKeyCredential(cfg["CONTENT_UNDERSTANDING_API_KEY"]),
    )
    # ── Alternative KEYLESS (Entra ID, khuyến nghị production) — thay cho AzureKeyCredential ──
    #   from azure.identity import DefaultAzureCredential
    #   client = ContentUnderstandingClient(
    #       endpoint=cfg["CONTENT_UNDERSTANDING_ENDPOINT"],
    #       credential=DefaultAzureCredential(),
    #   )
    #   (keyless chạy được khi principal có đúng RBAC data-plane role cho service này —
    #    vd Cognitive Services User trên resource Content Understanding; xem lab 00/04)

    # AUDIO: phiên âm + phân đoạn (cùng một API begin_analyze, đổi analyzer_id)
    audio_poller = client.begin_analyze(
        analyzer_id="prebuilt-audioSearch",
        inputs=[AnalysisInput(url=SAMPLE_AUDIO_URL)],
    )
    audio_result: AnalysisResult = audio_poller.result()
    print("Audio markdown:\n", audio_result.contents[0].markdown[:300])

    # VIDEO: phân tích phân cảnh + tóm tắt nội dung
    video_poller = client.begin_analyze(
        analyzer_id="prebuilt-videoSearch",
        inputs=[AnalysisInput(url=SAMPLE_VIDEO_URL)],
    )
    video_result: AnalysisResult = video_poller.result()
    print("\nVideo markdown:\n", video_result.contents[0].markdown[:300])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
