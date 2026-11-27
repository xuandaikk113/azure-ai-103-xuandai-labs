"""Điểm chạy CLI: chat liên tục với trợ lý (handoff orchestration).

Chạy: uv run python -m assistant.app   (cần PYTHONPATH trỏ src/, hoặc chạy từ module này)
"""

import asyncio
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")   # in tiếng Việt an toàn trên Windows
except Exception:
    pass

from .config import get_settings
from .chat_client import build_chat_client
from .router import AssistantRouter


async def run_cli() -> None:
    settings = get_settings()
    router = AssistantRouter(build_chat_client(settings))
    print(f"Trợ lý sẵn sàng (provider={settings.llm_provider}). Gõ 'quit' để thoát.")
    while True:
        try:
            message = input("\nBạn > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n(Đã dừng)")
            break
        if message.lower() in {"quit", "exit", "thoat", ""}:
            break
        intent, reply = await router.handle(message)
        print(f"[{intent}] Bot > {reply}")


def main() -> None:
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
