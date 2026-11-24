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
        # 1) Tạo conversation (server GIỮ lịch sử — khác lab 04/01 stateless)
        conversation = openai_client.conversations.create(
            items=[{"type": "message", "role": "user", "content": "Thủ đô Việt Nam là gì?"}],
        )
        print("conversation id:", conversation.id)

        # 2) Sinh câu trả lời dựa trên conversation (không cần gửi lại lịch sử)
        r1 = openai_client.responses.create(model=model, conversation=conversation.id)
        print("Lượt 1:", r1.output_text)

        # 3) Thêm lượt hỏi mới vào conversation rồi trả lời tiếp (server tự nhớ ngữ cảnh)
        openai_client.conversations.items.create(
            conversation_id=conversation.id,
            items=[{"type": "message", "role": "user", "content": "Thành phố đó có gì nổi tiếng?"}],
        )
        r2 = openai_client.responses.create(model=model, conversation=conversation.id)
        print("Lượt 2:", r2.output_text)

        # 4) Dọn dẹp
        openai_client.conversations.delete(conversation_id=conversation.id)
        print("Đã xoá conversation.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"[LỖI] {type(exc).__name__}: {exc}")
