"""
====================================================================
LAB 04/02 · Hội thoại server-managed: Conversations API (Foundry)
--------------------------------------------------------------------
Dịch vụ      : Microsoft Foundry (Conversations + Responses)
Biến .env    : FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
SDK tiền nhiệm: Threads/Runs của Assistants API cũ -> nay là Conversations API.
Chạy         : uv run 04_agent_conversation_management/02_conv_server_managed_threads_and_runs.py
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
from azure.identity import DefaultAzureCredential

# ── SDK ─────────────────────────────────────────────────────────
from azure.ai.projects import AIProjectClient   # get_openai_client() -> dùng Conversations/Responses


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
    cfg = require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")
    model = cfg["FOUNDRY_MODEL"]

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"], credential=credential) as project,
        project.get_openai_client() as openai_client,
    ):
        # 1) Tạo conversation RỖNG (server GIỮ lịch sử — khác lab 04/01 stateless)
        conversation = openai_client.conversations.create()
        print("conversation id:", conversation.id)

        # 2) Vòng lặp chat LIÊN TỤC ở CLI — gõ câu hỏi, 'quit'/'exit' để thoát.
        #    Mỗi lượt: thêm message của user vào conversation rồi gọi responses.create.
        #    Không cần gửi lại lịch sử — server tự nhớ ngữ cảnh qua conversation.id.
        print("Bắt đầu chat (gõ 'quit' / 'exit' để dừng).")
        try:
            while True:
                user_message = input("\nBạn > ").strip()
                if user_message.lower() in {"quit", "exit", "thoat", ""}:
                    break
                openai_client.conversations.items.create(
                    conversation_id=conversation.id,
                    items=[{"type": "message", "role": "user", "content": user_message}],
                )
                assistant_response = openai_client.responses.create(
                    model=model, conversation=conversation.id,
                )
                print("Bot >", assistant_response.output_text)
        except (EOFError, KeyboardInterrupt):
            print("\n(Đã dừng bằng Ctrl-C / EOF)")

        # 3) Dọn dẹp
        openai_client.conversations.delete(conversation_id=conversation.id)
        print("Đã xoá conversation.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
