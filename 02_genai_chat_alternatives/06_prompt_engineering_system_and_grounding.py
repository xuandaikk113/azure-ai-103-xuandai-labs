"""
====================================================================
LAB 02/06 · Prompt engineering: system message, few-shot, grounding, tham số
--------------------------------------------------------------------
Dịch vụ      : Azure OpenAI
Biến .env    : AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT
SDK tiền nhiệm: không.
Chạy         : uv run 02_genai_chat_alternatives/06_prompt_engineering_system_and_grounding.py
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


def ask(client, deployment, messages, **params):
    """Gọi model với bộ messages + tham số tuỳ biến, trả text."""
    r = client.chat.completions.create(model=deployment, messages=messages, **params)
    return r.choices[0].message.content


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
    deployment = cfg["AZURE_OPENAI_CHAT_DEPLOYMENT"]
    question = "Phí vận chuyển là bao nhiêu?"

    # ── 1) SYSTEM MESSAGE định hình vai trò/giọng điệu ──
    print("== System prompt ==")
    print(ask(client, deployment, [
        {"role": "system", "content": "Bạn là CSKH lịch sự, luôn trả lời bằng tiếng Việt."},
        {"role": "user", "content": question},
    ]))

    # ── 2) FEW-SHOT: cho ví dụ mẫu để model bắt chước định dạng ──
    print("\n== Few-shot ==")
    print(ask(client, deployment, [
        {"role": "system", "content": "Trả lời theo mẫu: 'Đáp: <nội dung>'."},
        {"role": "user", "content": "Giờ mở cửa?"},
        {"role": "assistant", "content": "Đáp: 8h–17h các ngày trong tuần."},
        {"role": "user", "content": question},
    ]))

    # ── 3) GROUNDING: chèn dữ liệu thật vào context để giảm 'bịa' ──
    print("\n== Grounding ==")
    knowledge = "Chính sách: phí ship 30.000đ, miễn phí cho đơn trên 500.000đ."
    print(ask(client, deployment, [
        {"role": "system", "content": f"Chỉ trả lời dựa trên dữ liệu sau:\n{knowledge}"},
        {"role": "user", "content": question},
    ]))

    # ── 4) THAM SỐ: temperature thấp = ổn định; cao = đa dạng ──
    print("\n== temperature=0 vs 1 ==")
    msg = [{"role": "user", "content": "Đặt 1 tên shop bán hoa."}]
    print("t=0:", ask(client, deployment, msg, temperature=0))
    print("t=1:", ask(client, deployment, msg, temperature=1))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
