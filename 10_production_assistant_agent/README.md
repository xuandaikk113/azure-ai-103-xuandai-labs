# 10 · Production Assistant Agent

Trợ lý **production-ready** dựng bằng **Microsoft Agent Framework** theo mẫu **handoff orchestration**:
một `triage` agent phân loại intent rồi **chuyển giao (handoff)** cho specialist agent phù hợp.
Mục tiêu: học **best practices** (chia module, tách tool, test, deploy) thay vì các file lab rời rạc.

## Kiến trúc

```
Người dùng
   │
   ▼
triage agent ──(phân loại intent)──► specialist agent ──► tool
   qa / chitchat / meetings / docs / worklog / web / sales
```

| Intent    | Specialist làm gì          | Tool                         |
|-----------|----------------------------|------------------------------|
| qa        | Hỏi đáp kiến thức chung     | — (chỉ model)                |
| chitchat  | Tán gẫu                    | — (chỉ model)                |
| meetings  | Đặt phòng họp              | `book_meeting` → mock API    |
| docs      | Tra tài liệu nội bộ        | `search_internal_docs` → local |
| worklog   | Ghi nhận giờ công việc     | `log_work` → mock API        |
| web       | Tìm internet               | `search_web` → OpenAI web_search |
| sales     | Phân tích bán hàng + chart | `analyze_sales` → text2sql + matplotlib |

## Cấu trúc thư mục

```
src/assistant/
  config.py          # cấu hình tập trung (env)
  chat_client.py     # dựng FoundryChatClient / OpenAIChatClient
  specialists.py     # các specialist agent
  router.py          # handoff orchestration (triage -> specialist)
  app.py             # CLI chat
  host.py            # HTTP /responses (deploy)
  tools/             # book_meeting, log_work, search_internal_docs, search_web, analyze_sales
mock_api/server.py   # FastAPI giả lập API đặt phòng / log work (offline)
data/                # seed_sales_db.py, internal_docs/
tests/               # unit test offline (không cần LLM)
Dockerfile, deploy/  # deploy Azure Container Apps
```

## Chạy local (offline, chỉ cần creds model)

```bash
# từ thư mục repo gốc (XuanDai-Labs) — dùng chung uv env
cp 10_production_assistant_agent/.env.example 10_production_assistant_agent/.env   # điền FOUNDRY_*

# 1) tạo DB bán hàng mẫu
uv run python 10_production_assistant_agent/data/seed_sales_db.py

# 2) chạy mock API (terminal riêng)
uv run uvicorn mock_api.server:app --app-dir 10_production_assistant_agent --port 8000

# 3) chat CLI
uv run python -m assistant.app     # (đặt PYTHONPATH=10_production_assistant_agent/src)
```

> Tool đặt phòng/log work gọi mock API local; text2sql chạy trên SQLite local; web_search gọi
> ra ngoài nếu có `AZURE_OPENAI_ENDPOINT`, không thì trả kết quả giả lập.

## Test

```bash
uv run pytest 10_production_assistant_agent/tests -q
```

Test chạy **hoàn toàn offline** (bơm SQL generator giả, dùng DB/docs tạm) — không gọi LLM/network.

## Deploy (Azure Container Apps)

```bash
bash 10_production_assistant_agent/deploy/deploy_container_apps.sh
```

Dùng **managed identity + keyless** (không secret) để gọi Foundry; nhớ gán role **Foundry User**
cho managed identity của app (xem lab `00/04`).

## Điểm học (best practices thể hiện ở đây)

- **Handoff orchestration** tường minh, dễ test/giám sát hơn 1 mega-agent.
- **Tách tool khỏi logic cốt lõi** (`search_docs`, `sql_from_question`…) để unit test không cần LLM.
- **Bảo mật**: text2sql chỉ cho phép `SELECT` (chặn INSERT/UPDATE/DELETE/DROP).
- **Keyless-first**, cấu hình tập trung, provider đổi được (Foundry ↔ Azure OpenAI).
