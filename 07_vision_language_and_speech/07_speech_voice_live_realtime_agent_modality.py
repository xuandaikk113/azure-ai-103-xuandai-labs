"""
====================================================================
LAB 07/07 · Voice Live: giọng nói thời gian thực (speech-to-speech)
--------------------------------------------------------------------
Dịch vụ      : Azure AI Voice Live
Biến .env    : SPEECH_KEY, SPEECH_REGION (hoặc FOUNDRY_PROJECT_ENDPOINT + keyless)
SDK tiền nhiệm: ghép tay azure-cognitiveservices-speech (STT) + LLM + TTS -> nay hợp nhất 1 SDK.
Chạy         : uv run 07_vision_language_and_speech/07_speech_voice_live_realtime_agent_modality.py
⚠ Lưu ý      : azure-ai-voicelive là SDK GA 1.0 nhưng ASYNC-ONLY (cài kèm [aiohttp]).
               Khung dưới đây là SKELETON có chú thích — đối chiếu sample azure-ai-voicelive
               trên Microsoft Learn cho tên hàm connect/session chính xác.
====================================================================
"""

# ── stdlib ──────────────────────────────────────────────────────
import os
import sys
import asyncio                  # Voice Live chạy bất đồng bộ (websocket realtime)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── nạp .env ────────────────────────────────────────────────────
from dotenv import load_dotenv

# ── xác thực ────────────────────────────────────────────────────
from azure.core.credentials import AzureKeyCredential

# ── SDK Voice Live (async) ──────────────────────────────────────
# azure-ai-voicelive: kết nối websocket realtime, hợp nhất STT + LLM + TTS.
from azure.ai.voicelive.aio import connect   # async client (cài: azure-ai-voicelive[aiohttp])


def require_env(*names: str) -> dict:
    load_dotenv()
    values, missing = {}, []
    for name in names:
        value = os.getenv(name)
        (values.__setitem__(name, value) if value else missing.append(name))
    if missing:
        sys.exit(f"[THIẾU CẤU HÌNH] Thêm vào .env: {', '.join(missing)}")
    return values


async def main() -> None:
    cfg = require_env("SPEECH_KEY", "SPEECH_REGION")

    # Mở phiên realtime (async context manager). Trong phiên:
    #   - stream audio micro VÀO -> model nghe
    #   - nhận audio RA -> phát loa (speech-to-speech)
    #   - có thể gắn model/agent để trả lời bằng giọng
    async with connect(
        endpoint=f"wss://{cfg['SPEECH_REGION']}.voice.live.azure.com",
        credential=AzureKeyCredential(cfg["SPEECH_KEY"]),
        model="gpt-4o-realtime-preview",
    ) as session:
        # TODO (theo sample): cấu hình session (voice, modality audio), rồi vòng lặp
        # gửi/nhận event audio. Dừng khi người dùng kết thúc.
        print("Đã mở phiên Voice Live:", session)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
