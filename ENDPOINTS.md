# ENDPOINTS.md — Bảng tra endpoint, scope & SDK (AI-103)

> Gom mọi URL/endpoint/token-scope hay nhầm vào một chỗ. Giải nghĩa thuật ngữ: `GLOSSARY.html`.
> Biến `.env`: `.env.example`. Thao tác tay trên Portal: các file `*.html` cạnh lab.

## 1. Hai Portal (giao diện web — KHÔNG dùng trong code)

| Portal | URL | Dùng để | File hướng dẫn |
|--------|-----|---------|----------------|
| **Azure Portal** | `portal.azure.com` | Tạo resource, **RBAC/IAM**, networking (VNet, private endpoint), quota, cost, key/endpoint | `00_azure_foundations/*.html` |
| **Microsoft Foundry Portal** (cũ: *Azure AI Foundry*) | `ai.azure.com` | Project, deploy model, Playground, agent + tools, Content Safety, Foundry IQ, evaluation, tracing | `01/`,`03/`,`06/`,`07/` `*.html` |

Hai portal dùng chung **Entra ID**. Foundry resource tạo ở `ai.azure.com` vẫn hiện trong `portal.azure.com`.

## 1b. Studio — web UI thử nhanh từng dịch vụ (đang gộp vào Foundry, 2026)

> **Xu hướng 2026:** Microsoft đang **gộp các Studio đứng riêng vào Microsoft Foundry Portal** (`ai.azure.com`).
> Chỗ "thử trực tiếp trên web" nên ưu tiên dùng **Playgrounds trong Foundry** (Build → Playgrounds).
> Các URL Studio cũ phần lớn **vẫn mở được nhưng redirect / sắp retire** — nhớ cho đỡ lạc, đừng phụ thuộc lâu dài.

| Studio | URL | Trạng thái 2026 (đã xác minh Microsoft Learn, 24/11/2026) | Thử gì |
|--------|-----|----------------------------------------------------------|--------|
| **Foundry Playgrounds** | `ai.azure.com` → Build → Playgrounds | ✅ **Nhà mới** của hầu hết playground | Chat, agent, model, image, speech, vision… |
| Speech Studio | `aka.ms/speechstudio/` | ✅ **Còn chạy**, Foundry chỉ là lựa chọn thêm (chưa có ngày retire) | STT, TTS, SSML, custom/voice gallery, pronunciation |
| Document Intelligence Studio | `documentintelligence.ai.azure.com/studio` | ⏳ **Còn chạy**, đang migrate 1 phần vào Foundry; feature ≤11/2024 + **custom classification vẫn chỉ ở Studio** | Layout, prebuilt (invoice/ID), custom model |
| Language Studio | `language.azure.com` | ⏳ Còn chạy, **migrate vào Foundry 20/03/2027** | NER, PII, sentiment, CLU, summarization |
| Content Safety Studio | *(không còn URL riêng)* → `ai.azure.com` | 🔁 Docs chuyển sang **"Foundry (classic)"**; thử tại Foundry portal | Lọc text/image có hại, severity |
| Vision Studio | `portal.vision.cognitive.azure.com` | 🔁 Redirect vào Foundry / đang retire *(nguồn Q&A)* | Image Analysis, OCR/Read, objects |
| Custom Vision | `customvision.ai` | ⚠️ **ĐANG RETIRE — hỗ trợ đến 25/09/2028**; thay bằng AML AutoML / Foundry Models / Content Understanding | Train classifier/object detection custom |

> ✅ còn chạy ổn · ⏳ còn chạy nhưng đã có lộ trình migrate (có/không ngày) · 🔁 không còn studio riêng, dùng trong Foundry · ⚠️ sắp khai tử (có ngày cụ thể). Tất cả xác minh qua trang Learn của từng dịch vụ (ms.date 2026). Lưu ý: Document Intelligence Studio **có đuôi `/studio`**; sovereign cloud dùng domain `formrecognizer.appliedai.azure.us|cn/studio`.

## 2. Endpoint dịch vụ (dùng trong code) — theo đuôi domain

Nhìn **đuôi domain** để biết loại endpoint và scope token keyless tương ứng:

| Đuôi domain | Loại | Token scope (keyless) | Dịch vụ |
|-------------|------|-----------------------|---------|
| `*.services.ai.azure.com` | Foundry project / AI Services | `https://ai.azure.com/.default` | Foundry project, Content Understanding |
| `*.openai.azure.com` | Azure OpenAI / Foundry Models | `https://ai.azure.com/.default` | Chat, embedding, image, Foundry Models /v1 |
| `*.cognitiveservices.azure.com` | AI Services (đa dịch vụ) | `https://cognitiveservices.azure.com/.default` | Vision, Language, Content Safety, Document Intelligence |
| `*.search.windows.net` | Azure AI Search | `https://search.azure.com/.default` | RAG index, knowledge base |
| `*.cognitive.microsofttranslator.com` | Translator | (thường dùng key + region) | Translator |
| `*.queue.core.windows.net` | Storage Queue | `https://storage.azure.com/.default` | Agent Azure Functions tool |

> `cognitiveservices` (số nhiều, có `s`) là tên **miền tài nguyên**; `Cognitive Services` là tên thương hiệu cũ của **Azure AI Services** — cùng gốc tên.

## 3. GenAI / Chat — MỚI vs CŨ (hay ra thi)

| Cách | base_url / client | api_version | Ghi chú |
|------|-------------------|-------------|---------|
| **Khuyến nghị (mới)** | `OpenAI(base_url="https://<res>.openai.azure.com/openai/v1/")` | **KHÔNG có** | `.env`: `AZURE_OPENAI_ENDPOINT` (+ nối `/openai/v1/`) |
| Cổ điển | `AzureOpenAI(azure_endpoint=..., api_version="2025-04-01-preview")` | **BẮT BUỘC** | Còn hợp lệ, không deprecated; giữ 1 file làm tham chiếu |
| ❌ Đã retire 2026-08-26 | `azure-ai-inference` (`ChatCompletionsClient`) | — | **KHÔNG dùng** → thay bằng OpenAI SDK /v1 |

Foundry Models non-OpenAI (Llama/Mistral/DeepSeek/Cohere) cũng gọi qua **OpenAI SDK /v1** cùng pattern — `FOUNDRY_MODELS_ENDPOINT`.

## 4. Token scope keyless (nhớ cho đúng scope)

```python
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
# Azure OpenAI / Foundry Models (/v1, openai SDK):  (verified Microsoft Learn 2026-10)
token = get_bearer_token_provider(DefaultAzureCredential(), "https://ai.azure.com/.default")
# Foundry project (AIProjectClient) / Content Understanding:
#   scope = "https://ai.azure.com/.default"
# AI Services khác keyless — Vision/Language/Content Safety/Document Intelligence (*.cognitiveservices.azure.com):
#   scope = "https://cognitiveservices.azure.com/.default"
# Azure AI Search:
#   scope = "https://search.azure.com/.default"
```
> ⚠️ Dễ nhầm: Azure OpenAI /v1 dùng **`ai.azure.com/.default`** (KHÔNG phải `cognitiveservices.azure.com/.default`).
> Scope `cognitiveservices.azure.com/.default` là cho các AI service khác (Vision/Language/…), không phải OpenAI /v1.

OpenAI /v1 keyless: truyền token provider vào tham số `api_key=` (SDK tự refresh).

## 5. Endpoint theo service — endpoint shape, biến .env, lab, SDK

| Dịch vụ | Endpoint shape | `.env` | Lab | SDK chính |
|---------|----------------|--------|-----|-----------|
| Foundry project (agents) | `https://<res>.services.ai.azure.com/api/projects/<proj>` | `FOUNDRY_PROJECT_ENDPOINT` | 03,04,05,06 | `azure-ai-projects` |
| Azure OpenAI | `https://<res>.openai.azure.com/` | `AZURE_OPENAI_ENDPOINT` | 01,02,06,07 | `openai` |
| Foundry Models /v1 | `https://<res>.openai.azure.com/openai/v1/` | `FOUNDRY_MODELS_ENDPOINT` | 02 | `openai` |
| AI Search | `https://<res>.search.windows.net` | `AZURE_SEARCH_ENDPOINT` | 06 | `azure-search-documents` |
| Content Safety | `https://<res>.cognitiveservices.azure.com/` | `CONTENT_SAFETY_ENDPOINT` | 01 | `azure-ai-contentsafety` |
| Vision (Image Analysis) | `https://<res>.cognitiveservices.azure.com/` | `VISION_ENDPOINT` | 07 | `azure-ai-vision-imageanalysis` |
| Language (Text + CLU) | `https://<res>.cognitiveservices.azure.com/` | `LANGUAGE_ENDPOINT` | 07 | `azure-ai-textanalytics` / `-language-*` |
| Translator | `https://api.cognitive.microsofttranslator.com/` | `TRANSLATOR_ENDPOINT` (+ `TRANSLATOR_REGION`) | 07 | `azure-ai-translation-text` |
| Speech | *(không endpoint — dùng key + region)* | `SPEECH_KEY`,`SPEECH_REGION` | 07 | `azure-cognitiveservices-speech` |
| Document Intelligence (cũ: Form Recognizer) | `https://<res>.cognitiveservices.azure.com/` | `DOC_INTELLIGENCE_ENDPOINT` | 08 | `azure-ai-documentintelligence` |
| Content Understanding | `https://<res>.services.ai.azure.com/` | `CONTENT_UNDERSTANDING_ENDPOINT` | 08 | `azure-ai-contentunderstanding` |
| Storage Blob | `https://<acct>.blob.core.windows.net` | `BLOB_CONNECTION_STRING` | 00,06,07 | `azure-storage-blob` |
| Storage Queue | `https://<acct>.queue.core.windows.net` | `STORAGE_QUEUE_SERVICE_ENDPOINT` | 03 | `azure-storage-queue` |
| App Insights (tracing) | *(connection string, không URL)* | `APPLICATIONINSIGHTS_CONNECTION_STRING` | 09 | `azure-monitor-opentelemetry` |
| ARM (deploy/fine-tune) | `https://management.azure.com` (mặc định trong SDK) | `AZURE_SUBSCRIPTION_ID`,`AZURE_RESOURCE_GROUP` | 01 | `azure-mgmt-*` |

## 6. Connection ID (không phải URL) — tool của agent

Vài tool agent cần **Connection ID** lấy ở Foundry Portal (Management → Connected resources), không phải endpoint URL:

| Biến | Dùng cho | Lab |
|------|----------|-----|
| `AI_SEARCH_PROJECT_CONNECTION_ID` | Azure AI Search tool | 06/05 |
| `BING_PROJECT_CONNECTION_ID` | Bing grounding tool | 03/07 |
| `MCP_SERVER_URL` | MCP tool (URL server MCP, không phải Azure) | 03 |

---
> Tài liệu học — không phải nguồn chính thức. Endpoint/scope có thể đổi theo region/bản SDK; đối chiếu Microsoft Learn khi nghi ngờ.
