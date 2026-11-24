# COVERAGE.md — Bản đồ lab ↔ Skills measured AI-103

Đối chiếu với **study guide chính thức** (skills measured *as of April 16, 2026*).
Mục đích: biết mỗi kỹ năng thi được phủ bởi file nào, và **chỗ nào còn trống**.

> Nguồn: https://learn.microsoft.com/credentials/certifications/resources/study-guides/ai-103
> ✅ có lab · 🟡 phủ một phần / ghép nhiều lab · ❌ chưa có (xem "Gap còn lại")

---

## 1. Plan and manage an Azure AI solution — **25–30%**
| Sub-skill | Phủ bởi |
|-----------|---------|
| Chọn Foundry services / model (LLM, SLM, multimodal, Foundry Tools) | 🟡 `01/02-04`, `02/03` + lý thuyết PLAN |
| Chọn phương pháp retrieval/indexing | ✅ `06/01-04` |
| Chọn memory/tool/knowledge cho agent | ✅ `03/*`, `04/05` |
| Thiết kế hạ tầng, deployment options, cấu hình deployment | ✅ `01/02`, `01/03`, `01/04` |
| Tích hợp CI/CD cho Foundry project | ✅ `.github/workflows/deploy-foundry.yml` + `foundations §6` |
| Quota, scaling, rate limit, cost | 🟡 `01/02` |
| Monitor performance, drift, safety, grounding | ✅ `09/01`, `09/02` |
| Monitor ingestion/search index health | 🟡 `06/03` |
| Security: managed identity, keyless, RBAC | ✅ `01/01`, `00/02` + `foundations §2-3` (Web UI + code) |
| Security: private networking | 🟡 `azure_foundations.html §4` (kiến thức + diagram) |
| Responsible AI: safety filter, guardrail, moderation | ✅ `01/05` |
| Responsible AI: evaluators, safety evaluation | ✅ `01/05`, `09/02` |
| Auditing: trace logging, provenance, approval workflow | 🟡 `09/01`, `03/02` (approval) |
| Govern agent: oversight mode, tool-access control | 🟡 `03/02`, `03/04` |

## 2. Implement generative AI and agentic solutions — **30–35%**
| Sub-skill | Phủ bởi |
|-----------|---------|
| Deploy/consume LLM, SLM, code, multimodal | ✅ `01/02-03`, `02/01-05` |
| RAG trong ứng dụng | ✅ `06/01-05` |
| Workflow, tool-augmented flow, multistep reasoning | ✅ `05/01`, `03/02-03` |
| Evaluate model/app (fabrication, relevance, quality, safety) | ✅ `01/05`, `09/02` |
| Tích hợp qua Foundry SDK/connector; connect app ↔ project | ✅ `01/04`, `02/03` |
| Agent: role/goal/conversation/tool schema | ✅ `03/01-02`, `04/*` |
| Agent: retrieval + function-calling + memory | ✅ `03/02`, `06/05`, `04/05` |
| Agent tools: API, knowledge, search, content understanding, custom fn | ✅ `03/02-04`, `03/07-09`, `06/05` |
| Multi-agent orchestration | ✅ `05/01-05` |
| Autonomous/semi-auto workflow + approval | ✅ `03/02`, `05/*` |
| Monitor agent, evaluate behavior, error analysis | ✅ `09/01-02` |
| Prompt engineering + model parameters | ✅ `02/06` |
| Reflection, chain-of-thought, self-critique | ✅ `05/05` |
| Observability: tracing, token analytics, safety, latency | ✅ `09/01` |
| Orchestrate nhiều model / hybrid LLM + rules | 🟡 `05/*` |

## 3. Implement computer vision solutions — **10–15%**
| Sub-skill | Phủ bởi |
|-----------|---------|
| Tạo ảnh từ text + reference, image editing/inpainting | ✅ `07/08` |
| Tạo video từ text + reference, video editing | ✅ `07/09` |
| Phân tích visual bằng multimodal model | ✅ `02/05`, `07/01` |
| Caption ngắn/chi tiết cho ảnh | ✅ `07/01` |
| Visual question-answering grounded | 🟡 `02/05` |
| Alt-text / mô tả mở rộng (accessibility) | 🟡 `07/01` (cần nhấn mạnh khi viết) |
| Content Understanding trích đặc trưng visual, video | ✅ `08/04` |
| Single-task & pro-mode CU pipeline | 🟡 `08/03-05` |
| Nhận diện object/region trong ảnh/video | ✅ `07/02` |
| Filter nội dung visual không an toàn | ✅ `01/05` |
| Indirect prompt injection qua text trong ảnh | 🟡 `02/05` (note) |
| Visual policy: watermark, symbol cấm, brand | ❌ **Gap** (nhẹ) |

## 4. Implement text analysis solutions — **10–15%**
| Sub-skill | Phủ bởi |
|-----------|---------|
| Entity/topic/summary/structured JSON (generative prompting + Foundry Tools) | ✅ `02/04`, `02/06`, `07/03-04` |
| Sentiment, tone, safety, sensitive content | ✅ `07/03`, `01/05` |
| Translate (Translator hoặc LLM flow) | ✅ `07/05` |
| Customize output cho domain (compliance summary, domain extraction) | 🟡 `02/06`, `07/04` |
| Speech ↔ text cho agentic interaction | ✅ `07/06` |
| Speech làm agent modality + custom speech | ✅ `07/07` |
| Multimodal reasoning từ audio | ✅ `02/05`, `07/07` |
| Dịch speech sang ngôn ngữ khác | ✅ `07/07` |

## 5. Implement information extraction solutions — **10–15%**
| Sub-skill | Phủ bởi |
|-----------|---------|
| Ingest/index documents, images, audio, video | ✅ `06/03`, `08/04` |
| Semantic/hybrid/vector search cho grounding | ✅ `06/01-02` |
| Enrichment custom/built-in skills (text/image/layout) | ✅ `06/03` |
| RAG ingestion + OCR | ✅ `06/03`, `08/01` |
| Nối retrieval vào workflow/agent tool | ✅ `06/05` |
| Trích tài liệu multimodal (OCR + layout + field) | ✅ `08/01-02` |
| Clean/grounded representation bằng Content Understanding | ✅ `08/03-04` |
| Analyzer sinh structured/markdown bằng CU | ✅ `08/05` |

---

## Gap — đã xử lý / còn lại
| Mục | Nhóm | Trạng thái |
|-----|------|-----------|
| CI/CD cho Foundry project | 1 | ✅ `.github/workflows/deploy-foundry.yml` + `foundations §6` |
| Private networking / infra security | 1 | ✅ `azure_foundations.html §4` (kiến thức + diagram) |
| Fundamentals (resource hierarchy, Entra) | 1 | ✅ `azure_foundations.html §1-2` |
| RBAC Web UI + code | 1 | ✅ `foundations §3` + lab `00/02` |
| Tạo blob storage (provisioning) | 1/5 | ✅ lab `00/01` + `foundations §5` |
| Visual policy (watermark/symbol/brand) | 3 | 🟡 còn lại — gộp note vào `07/08` hoặc tách lab (bạn quyết) |
| Alt-text/accessibility, visual QA, prompt-injection-in-image | 3 | 🟡 ở mức "note" trong `07/01`, `02/05` — nhấn mạnh khi viết |

> Nhận định: **5/5 nhóm kỹ năng đều có lab**; nhóm trọng số cao (1 và 2) phủ dày. Kiến thức hạ tầng
> (fundamentals, RBAC, networking, CI/CD) đã có trong `00_azure_foundations/`. Gap còn lại chỉ là vài
> chủ đề responsible-AI cho vision, đang ở mức ghi chú.
