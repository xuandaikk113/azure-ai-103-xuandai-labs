"""
====================================================================
LAB 07/09 · Video generation (text-to-video) — ví dụ Sora trên Foundry
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI / Foundry (model video, vd Sora)
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_VIDEO_DEPLOYMENT (v1: bỏ api_version)
SDK tiền nhiệm: không.
Chạy         : uv run 07_vision_language_and_speech/09_vision_video_generation_and_editing.py
⚠ Lưu ý      : Tạo video là tác vụ LONG-RUNNING (job). API video có thể khác giữa các bản —
               đối chiếu tài liệu Sora/Video trên Microsoft Learn; khung dưới minh hoạ luồng job.
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import time

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
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_VIDEO_DEPLOYMENT",
    )
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Cách KHUYẾN NGHỊ (v1). Nếu model video chưa có trong v1 GA, dùng AzureOpenAI + api_version preview.
    client = OpenAI(
        base_url=cfg["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1/",
        api_key=cfg["AZURE_OPENAI_API_KEY"],
    )

    # 1) Tạo job sinh video từ prompt (long-running)
    #    (tên API video tuỳ bản SDK; đây là luồng job tiêu biểu: create -> poll -> download)
    job = client.videos.create(
        model=cfg["AZURE_OPENAI_VIDEO_DEPLOYMENT"],
        prompt="Một con thuyền nhỏ trôi trên hồ lúc hoàng hôn, 5 giây",
    )
    print(f"Đã tạo video job: {getattr(job, 'id', job)}")

    # 2) Poll tới khi hoàn tất (giới hạn vài vòng để minh hoạ)
    for _ in range(3):
        time.sleep(10)
        job = client.videos.retrieve(job.id)
        print(f"  status={getattr(job, 'status', '?')}")
        if getattr(job, "status", "") in ("completed", "failed"):
            break

    # 3) Khi completed: tải video về assets/output (API download tuỳ bản).
    print("Khi completed: tải nội dung video về", OUTPUT_DIR)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
