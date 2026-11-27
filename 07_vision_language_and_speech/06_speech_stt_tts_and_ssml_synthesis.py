"""
====================================================================
LAB 07/06 · Speech: STT + TTS + SSML
--------------------------------------------------------------------
Dịch vụ      : Azure AI Speech
Biến .env    : SPEECH_KEY, SPEECH_REGION
SDK tiền nhiệm: không (azure-cognitiveservices-speech là SDK hiện hành).
Chạy         : uv run 07_vision_language_and_speech/06_speech_stt_tts_and_ssml_synthesis.py
Cần (STT)    : file assets/sample_audio.wav
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

# ── SDK Speech ──────────────────────────────────────────────────
# azure-cognitiveservices-speech: STT/TTS/translation giọng nói (import alias 'speechsdk').
import azure.cognitiveservices.speech as speechsdk


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
    cfg = require_env("SPEECH_KEY", "SPEECH_REGION")
    speech_config = speechsdk.SpeechConfig(subscription=cfg["SPEECH_KEY"], region=cfg["SPEECH_REGION"])
    # ── Alternative KEYLESS (Entra ID) — thay cho subscription key ──
    #   from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    #   token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    #   speech_config = speechsdk.SpeechConfig(auth_token="aad#{resourceId}#" + token_provider(), region=cfg["SPEECH_REGION"])
    #   (Speech yêu cầu định dạng auth_token đặc thù "aad#{resourceId}#{aadToken}" — {resourceId} là
    #    resource ID đầy đủ của Speech resource; principal cần role Cognitive Services User; xem lab 00/04)
    speech_config.speech_synthesis_voice_name = "vi-VN-HoaiMyNeural"   # giọng neural tiếng Việt

    # 1) TTS: text -> giọng nói (phát ra loa mặc định)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    synthesizer.speak_text_async("Xin chào, đây là bài lab tổng hợp giọng nói.").get()
    print("Đã phát TTS.")

    # 2) SSML: điều khiển ngữ điệu/tốc độ/ngắt nghỉ
    ssml = """
    <speak version='1.0' xml:lang='vi-VN'>
      <voice name='vi-VN-HoaiMyNeural'>
        Đọc chậm rãi <break time='400ms'/>
        <prosody rate='-20%' pitch='+10%'>và nhấn nhá hơn.</prosody>
      </voice>
    </speak>"""
    synthesizer.speak_ssml_async(ssml).get()
    print("Đã phát SSML.")

    # 3) STT: audio file -> text
    audio_path = os.path.join("assets", "sample_audio.wav")
    if os.path.exists(audio_path):
        audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        result = recognizer.recognize_once()
        print("STT:", result.text)
    else:
        print(f"(bỏ qua STT: chưa có {audio_path})")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
