# AGENTS.md — Luật dự án XuanDai-Labs (ôn thi Azure AI-103)

> File này là "luật" cho mọi agent/AI (Claude Code, Copilot, …) khi làm việc trong repo này.
> Người đọc chính vẫn là con người đang ôn thi, nên mọi thứ ưu tiên **dễ học, dễ nhớ**.

## 0. Bối cảnh

- Đây là project **thực hành (hands-on) để ôn thi chứng chỉ Azure AI-103** —
  *Developing AI Apps and Agents on Azure* (Microsoft Certified: Azure AI Apps and Agents
  Developer Associate — hiện ở trạng thái **beta** tính đến 11/2026).
- Mục tiêu: học kiến thức thi **bằng cách viết code chạy được**, mỗi phương án (alternative)
  để ở **một file Python riêng** thay vì gộp chung.

## 1. Ngôn ngữ & comment

- **Toàn bộ comment trong code viết bằng tiếng Việt.**
- **Tên hàm / biến / class BẮT BUỘC viết bằng tiếng Anh**; chỉ comment mới viết tiếng Việt.
  (vd: dùng `ask_model`, không dùng `hoi_model`; `get_exchange_rate`, không dùng `lay_ty_gia`.)
- Giải thích **ngắn gọn, đúng việc** cho từng dòng/đoạn code — đủ để sau này đọc lại là nhớ.
- Phần `import` **bắt buộc có comment**: giải thích package làm gì **và nhắc SDK tiền nhiệm nếu có**
  (ví dụ: `Form Recognizer → Document Intelligence`, `Azure Cognitive Search → Azure AI Search`,
  `Semantic Kernel` + `AutoGen` → `Microsoft Agent Framework`,
  `azure-ai-agents` (gói riêng) → đã gộp vào `azure-ai-projects`).

## 2. Mỗi file Python

- Là **standalone, chạy được**: đầy đủ `import`, `load_dotenv()`, khởi tạo client/biến, có `main()`
  và khối `if __name__ == "__main__":`.
- **Không** import chéo giữa các file lab (mỗi file tự lo mọi thứ của nó).
- Mỗi alternative = **một file riêng** (không viết nhiều cách trong cùng một file).
- Có header đầu file nêu: mục tiêu lab, dịch vụ Azure/Foundry dùng, biến `.env` cần, SDK tiền nhiệm.
- Có xử lý lỗi cơ bản và dọn dẹp tài nguyên (xoá agent/deployment test…) khi cần.

## 3. Quản lý thư viện

- Dùng **`uv`** thay cho `pip`. Thêm thư viện bằng `uv add <pkg>`, chạy bằng `uv run <file>.py`.
- Nguồn sự thật của dependency là **`pyproject.toml`** (do `uv` quản lý), **không** dùng `requirements.txt`.

## 4. SDK & phiên bản

- Luôn bám **SDK/API mới nhất theo Microsoft Learn (2026)**. Khi nghi ngờ API đổi, tra Microsoft Learn
  trước khi viết, **không đoán theo trí nhớ cũ**.
- Lưu ý một số đổi tên 2026 đã xác nhận:
  - Thương hiệu: *Azure AI Foundry* → **Microsoft Foundry**.
  - Agent: `azure-ai-agents` đã **gộp vào `azure-ai-projects` 2.x**; tạo agent qua
    `project_client.agents.create_version(...)`, gọi model/Responses qua `project_client.get_openai_client()`.
  - Agent Framework: cài `agent-framework-core` (lõi) / `agent-framework-foundry` (tích hợp Foundry); Python ≥ 3.10.
  - Inference: **`azure-ai-inference` đã DEPRECATED (retire 2026-08-26)** → dùng **OpenAI SDK** trỏ endpoint
    OpenAI/v1 (`https://<res>.openai.azure.com/openai/v1/`, token scope `https://ai.azure.com/.default`) cho
    cả Azure OpenAI lẫn Foundry Models (Llama/Mistral/DeepSeek/Cohere).
  - RAG mới: **Foundry IQ** (knowledge base + agentic retrieval) chạy trên Azure AI Search (`azure-search-documents`).

## 5. Git

- **KHÔNG** thêm dòng `Co-Authored-By: Claude …` (hay bất kỳ attribution AI nào) vào commit.
- Commit message tiếng Anh; mô tả đúng việc đã làm.

## 6. Cấu trúc repo

- `00_azure_foundations/` — nền tảng Azure (học trước): tài liệu **HTML có diagram** (fundamentals,
  RBAC, networking/security, CI/CD) + vài lab `.py` provisioning (storage, RBAC).
- 9 thư mục lab (`01_…` → `09_…`), mỗi thư mục chứa các file `NN_<ten>.py`.
- `.github/workflows/` — ví dụ CI/CD deploy Foundry. `assets/` — dữ liệu mẫu.
- File hỗ trợ ở gốc: `AGENTS.md` (luật), `PLAN.md` (kế hoạch từng file), `COVERAGE.md` (bản đồ kỹ năng thi),
  `_template.py`, `_smoke_check.py`, `.env.example`, `.python-version`, `pyproject.toml`, `README.md`.
- Nội dung không-cần-code (kiến thức hạ tầng, hướng dẫn Web UI) viết bằng **HTML/Markdown**, không nhất thiết `.py`.
- Xem **`PLAN.md`** (chi tiết từng file) và **`COVERAGE.md`** (map vào skills measured).
