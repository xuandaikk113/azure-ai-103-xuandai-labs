# XuanDai-Labs — Hands-on ôn thi Azure AI-103

Bộ **54 lab Python độc lập** (9 nhóm chủ đề + nền tảng `00`) để học kiến thức thi
**AI-103 – Developing AI Apps and Agents on Azure** bằng cách viết code chạy được.
Mỗi *alternative* (cách làm thay thế) nằm ở **một file riêng**. Python pin **3.12** (`.python-version`).

## Bắt đầu

```bash
uv sync                                   # tạo .venv + cài thư viện từ pyproject.toml
cp .env.example .env                      # rồi điền giá trị thật
uv run 02_genai_chat_alternatives/01_chat_azure_openai_sdk_completions.py
python _smoke_check.py                     # nghiệm thu: biên dịch mọi lab + check .env (KHÔNG gọi Azure)
```

## Tài liệu

- **`AGENTS.md`** — luật dự án (comment tiếng Việt, standalone, uv, SDK 2026…).
- **`PLAN.md`** — kế hoạch chi tiết **từng file**: mục tiêu, SDK (+ tiền nhiệm), biến `.env`, các bước, điểm nhớ.
- **`COVERAGE.md`** — bản đồ lab ↔ 5 nhóm kỹ năng thi (skills measured) + gap còn lại.
- **`GLOSSARY.html`** — tra 123 thuật ngữ (có ô search live) · **`MINDMAP.html`** — sơ đồ quan hệ hệ sinh thái.
- Mỗi lab Portal-relevant có **`<tên>.html`** cạnh file `.py` — hướng dẫn step-by-step trên Portal (modern Foundry UI).
- **`_template.py`** — khung chuẩn để copy khi tạo lab mới (đã ép stdout UTF-8 cho Windows).
- **`_smoke_check.py`** — kiểm tra nhanh toàn bộ lab.
- **`.env.example`** — biến môi trường mẫu · **`assets/`** — dữ liệu mẫu (xem `assets/README.md`).

## 8 nhóm lab

| # | Thư mục | Chủ đề |
|---|---------|--------|
| 00 | `00_azure_foundations` | Nền tảng Azure (HTML+diagram): fundamentals, RBAC, networking, CI/CD + provisioning |
| 01 | `01_foundry_setup_and_deployments` | Auth, deploy model (OpenAI/non-OpenAI), project, content safety |
| 02 | `02_genai_chat_alternatives` | Các cách gọi GenAI chat & multimodal |
| 03 | `03_build_and_deploy_agents` | Xây & deploy agent (Foundry Agent Service + Agent Framework) |
| 04 | `04_agent_conversation_management` | Quản lý hội thoại & bộ nhớ agent |
| 05 | `05_multi_agent_orchestration_patterns` | Điều phối multi-agent (các kiến trúc) |
| 06 | `06_rag_and_foundry_iq_grounding` | RAG, Azure AI Search, Foundry IQ |
| 07 | `07_vision_language_and_speech` | Vision, Language, Translator, Speech |
| 08 | `08_information_extraction` | Document Intelligence & Content Understanding |
| 09 | `09_observability_and_tracing` | Tracing (OpenTelemetry), monitoring & online evaluation |

## Lộ trình học gợi ý (learner path)
0. **Hạ tầng Azure** → mở `00_azure_foundations/azure_foundations.html` (tài nguyên, RBAC, networking, CI/CD) + provisioning `00/01-02`.
1. **Nền tảng Foundry** → `01` (auth keyless → deploy model → project → content safety).
2. **Gọi GenAI** → `02` (chat completions → Responses API → streaming/JSON → multimodal → prompt engineering).
3. **Agent cơ bản** → `03/01-03` (prompt agent → function tool → code interpreter/file search).
4. **Hội thoại & bộ nhớ** → `04`.
5. **Agent nâng cao & tools** → `03/04-09` (MCP/A2A, Agent Framework, hosted, Bing/OpenAPI/Functions).
6. **Multi-agent** → `05` (sequential → concurrent → handoff → supervisor → reflection).
7. **RAG & grounding** → `06`.
8. **Vision / Language / Speech** → `07` (phân tích → tạo ảnh/video → speech).
9. **Information extraction** → `08`.
10. **Vận hành** → `09` (tracing, monitoring). Đối chiếu `COVERAGE.md` để không bỏ sót.

> Trạng thái kỳ thi: AI-103 đang **beta** (tính đến 11/2026). Luôn đối chiếu
> [Study guide chính thức](https://learn.microsoft.com/credentials/certifications/resources/study-guides/ai-103)
> vì skills outline có thể còn đổi.
