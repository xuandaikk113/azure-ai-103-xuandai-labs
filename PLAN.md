# PLAN.md — Kế hoạch chi tiết từng file (59 lab)

> Dùng chung với `AGENTS.md`. Mỗi mục gồm: **Mục tiêu · SDK (+ tiền nhiệm) · ENV · Các bước · Thi nhớ**.
>
> **Khung chuẩn mọi file** (áp cho tất cả, không lặp lại ở từng mục):
>
> 1. Header docstring: mục tiêu lab + dịch vụ + biến `.env` cần + SDK tiền nhiệm.
> 2. `import` có comment từng nhóm (stdlib → dotenv → azure-identity → SDK dịch vụ).
> 3. `load_dotenv()` + đọc biến, kiểm tra thiếu biến thì báo lỗi rõ ràng.
> 4. Khởi tạo client (ưu tiên `DefaultAzureCredential`; nêu cả cách API key).
> 5. Logic chính (phần riêng của từng lab bên dưới).
> 6. In kết quả dễ đọc + `try/except` + dọn tài nguyên test.
> 7. `def main(): ...` và `if __name__ == "__main__": main()`.

---

## 00 · azure_foundations

> Nền tảng hạ tầng — **học trước**. Kiến thức không-cần-code ở **`azure_foundations.html`** (có diagram:
> cấu trúc tài nguyên, RBAC Web UI, networking); CI/CD mẫu ở **`.github/workflows/deploy-foundry.yml`**.
> Hai file `.py` dưới là provisioning bằng code.

### `01_provision_storage_blob.py`

- **Mục tiêu:** Tạo storage account + blob container bằng code (cho RAG / dịch document / fine-tune).
- **SDK:** `azure-mgmt-storage` (`StorageManagementClient`) + `azure-identity`.
- **ENV:** `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `STORAGE_ACCOUNT_NAME`, `AZURE_LOCATION`.
- **Các bước:** (1) tạo account (`begin_create`). (2) tạo container `documents`. (3) in endpoint/connection info.
- **Thi nhớ:** blob là nơi ingest/output dữ liệu; truy cập keyless qua role *Storage Blob Data Contributor*.

### `02_grant_rbac_role_assignment.py`

- **Mục tiêu:** Gán RBAC role cho principal (user / managed identity) bằng code.
- **SDK:** `azure-mgmt-authorization` (`AuthorizationManagementClient.role_assignments.create`) + `azure-identity`.
- **ENV:** `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `RBAC_PRINCIPAL_ID`, `RBAC_ROLE_NAME`.
- **Các bước:** (1) tra `role_definition_id` theo tên role. (2) tạo `RoleAssignment` (principal + role + scope). (3) xác nhận.
- **Thi nhớ:** RBAC = principal + role + scope (thừa kế xuống); least privilege. Web UI vs code xem `azure_foundations.html`.

### `03_rbac_scopes_and_builtin_roles.py`

- **Mục tiêu:** gán role ở các SCOPE khác nhau (subscription/rg/resource) + bảng built-in AI roles hay dùng.
- **SDK:** `azure-mgmt-authorization`. **ENV:** thêm `RBAC_SCOPE_LEVEL`, `RBAC_TARGET_RESOURCE_ID`.
- **Thi nhớ:** 4 cấp scope thừa kế xuống; chọn cấp thấp nhất đủ dùng. Built-in role Foundry (2026, đã đổi tên): *Foundry User* (cũ: Azure AI User), *Foundry Project Manager*, *Foundry Owner*, *Foundry Agent Consumer*; đừng dùng *Azure AI Developer* cho Foundry project. Data-plane khác: *Cognitive Services OpenAI User* (Azure OpenAI classic), *Search Index Data Reader/Contributor*, *Storage Blob Data …*.

### `04_rbac_managed_identity_keyless.py`

- **Mục tiêu:** gán role cho managed identity để app/agent gọi service keyless.
- **SDK:** `azure-mgmt-authorization` (principal_type=`ServicePrincipal`). **ENV:** `MI_PRINCIPAL_ID`, `RBAC_ROLE_NAME`.
- **Thi nhớ:** MI (system vs user-assigned) đều là ServicePrincipal; keyless chỉ chạy khi MI có role data-plane đúng, nếu không → 401/403.

### `05_rbac_custom_role_definition.py`

- **Mục tiêu:** tạo custom role (actions/dataActions) khi built-in không vừa, rồi (tuỳ chọn) gán.
- **SDK:** `role_definitions.create_or_update` + `RoleDefinition`/`Permission`. **ENV:** (tuỳ chọn) `RBAC_PRINCIPAL_ID`.
- **Thi nhớ:** `actions`=control plane, `dataActions`=data plane (keyless cần); `assignableScopes`; `roleType=CustomRole`.

### `06_rbac_list_check_remove.py`

- **Mục tiêu:** liệt kê/kiểm tra quyền của principal và xoá an toàn 1 assignment.
- **SDK:** `role_assignments.list_for_scope` / `.delete`. **ENV:** (tuỳ chọn) `RBAC_PRINCIPAL_ID`, `RBAC_ASSIGNMENT_NAME_TO_DELETE`.
- **Thi nhớ:** xoá assignment cần `name` (GUID); lọc `principalId eq '...'` để audit.

---

## 01 · foundry_setup_and_deployments

### `01_auth_api_key_vs_default_credential.py`

- **Mục tiêu:** So sánh 2 cách xác thực: API key (cứng) vs **keyless** `DefaultAzureCredential`.
- **SDK:** `azure-identity` (`DefaultAzureCredential`, `AzureCliCredential`, `get_bearer_token_provider`); `openai.AzureOpenAI`. *Tiền nhiệm:* trước đây hay hard-code key / dùng `azure-common`.
- **ENV:** `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_CHAT_DEPLOYMENT`.
- **Các bước:** (1) gọi 1 lần bằng `api_key`. (2) gọi lại bằng `DefaultAzureCredential` + `get_bearer_token_provider(..., "https://cognitiveservices.azure.com/.default")`. (3) bật logging chuỗi credential để thấy thứ tự thử (`EnvironmentCredential → ManagedIdentity → AzureCli`).
- **Thi nhớ:** keyless/Entra ID là best practice; scope token của Azure OpenAI.

### `02_deploy_openai_model_standard_and_ptu.py`

- **Mục tiêu:** Tạo/liệt kê deployment model OpenAI theo kiểu `Standard`, `GlobalStandard`, `ProvisionedManaged (PTU)` và xem quota.
- **SDK:** `azure-mgmt-cognitiveservices` (`CognitiveServicesManagementClient.deployments`) + `azure-identity`. *Tiền nhiệm:* thao tác tay trên portal / REST thuần.
- **ENV:** `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `AOAI_ACCOUNT_NAME`.
- **Các bước:** (1) `begin_create_or_update` deployment với `sku.name` = Standard/GlobalStandard/… + `capacity`. (2) list deployments + đọc `sku`, `capacity`. (3) in quota/rate limit; (4) (tuỳ chọn) xoá deployment test.
- **Thi nhớ:** phân biệt loại SKU, ý nghĩa PTU vs token-based, quota theo region.

### `03_deploy_non_openai_model_serverless_maas.py`

- **Mục tiêu:** Deploy & gọi model **non-OpenAI** (Llama/Mistral/DeepSeek/Cohere) qua Serverless API (MaaS) endpoint thống nhất.
- **SDK:** `openai` (`OpenAI`/`AzureOpenAI`) trỏ endpoint **OpenAI /v1** của Foundry. *Tiền nhiệm:* mỗi provider 1 SDK → `azure-ai-inference` (`ChatCompletionsClient`) gộp lại nhưng **đã deprecated/retire 2026-08-26** → nay dùng OpenAI SDK /v1.
- **ENV:** `FOUNDRY_MODELS_ENDPOINT` (dạng `.../openai/v1/`), `FOUNDRY_MODELS_API_KEY` (hoặc keyless scope `https://ai.azure.com/.default`), `FOUNDRY_NON_OPENAI_MODEL`.
- **Các bước:** (1) tạo serverless deployment (mô tả hoặc qua mgmt client). (2) `OpenAI(base_url=FOUNDRY_MODELS_ENDPOINT, ...)` rồi `chat.completions.create(model=<non-openai>)`. (3) in response + usage.
- **Thi nhớ:** Foundry Models dùng chung OpenAI /v1; một API cho cả OpenAI lẫn non-OpenAI.

### `04_inspect_foundry_project_and_connections.py`

- **Mục tiêu:** Kết nối Foundry project, liệt kê connected resources (AI Search, Storage, Key Vault), deployments.
- **SDK:** `azure-ai-projects` (`AIProjectClient`, `.connections`, `.deployments`). *Tiền nhiệm:* `azure-ai-resources`/portal.
- **ENV:** `FOUNDRY_PROJECT_ENDPOINT`.
- **Các bước:** (1) `AIProjectClient(endpoint, DefaultAzureCredential())`. (2) `.connections.list()` + lọc theo type. (3) `.deployments.list()`. (4) in cấu hình.
- **Thi nhớ:** project là trung tâm; connections dùng Entra ID; client chỉ hỗ trợ Entra ID auth.

### `05_content_safety_and_model_evaluation.py`

- **Mục tiêu:** Kiểm duyệt nội dung (severity 0/2/4/6) + chạy đánh giá chất lượng/an toàn.
- **SDK:** `azure-ai-contentsafety` (`ContentSafetyClient.analyze_text/analyze_image`) + `azure-ai-evaluation` (groundedness/relevance/coherence/safety). *Tiền nhiệm:* Content Moderator (đã retire).
- **ENV:** `CONTENT_SAFETY_ENDPOINT`, `CONTENT_SAFETY_API_KEY`.
- **Các bước:** (1) analyze_text với 4 category (Hate/SelfHarm/Sexual/Violence). (2) đọc `severity`. (3) chạy 1 evaluator (vd `RelevanceEvaluator`) trên cặp query/response.
- **Thi nhớ:** thang severity, 4 harm categories, blocklist, evaluators tích hợp Foundry.

### `06_finetune_model_customization.py`

- **Mục tiêu:** Fine-tune (customize) model cho domain riêng (vd phân loại/tone đặc thù).
- **SDK:** `openai` (`client.fine_tuning.jobs.create`) trên Azure OpenAI; `azure-mgmt-cognitiveservices` để deploy model đã fine-tune. *Tiền nhiệm:* fine-tune qua REST/portal.
- **ENV:** `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `AOAI_ACCOUNT_NAME`.
- **Các bước:** (1) upload file train/validation (JSONL). (2) tạo fine-tuning job → poll. (3) deploy model fine-tuned. (4) gọi thử.
- **Thi nhớ:** fine-tune ≠ RAG ≠ prompt; cần JSONL; model customization có chi phí hosting riêng.

### `07_auth_service_principal_client_secret.py`

- **Mục tiêu:** app NGOÀI Azure (on-prem/CI-CD) xác thực bằng **service principal** (app registration + client secret) rồi đọc Blob.
- **SDK:** `azure-identity` (`ClientSecretCredential`) + `azure-storage-blob` (`BlobServiceClient`). **ENV:** `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `STORAGE_ACCOUNT_NAME`.
- **Thi nhớ:** "App" = Application object (toàn cầu) + service principal (cục bộ, cái được gán quyền). Đối xứng 00/04 (MI): SP giữ secret & chạy mọi nơi; MI không secret & chỉ trên Azure; cả hai là `principal_type='ServicePrincipal'`.

---

## 02 · genai_chat_alternatives

### `01_chat_azure_openai_sdk_completions.py`

- **Mục tiêu:** Chat completion "cổ điển" qua `AzureOpenAI`/`AsyncAzureOpenAI`.
- **SDK:** `openai` (`AzureOpenAI`). *Tiền nhiệm:* `openai<1.0` kiểu `openai.ChatCompletion.create`; gói `azure-openai` cũ.
- **ENV:** `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_CHAT_DEPLOYMENT` (+ key hoặc token provider).
- **Các bước:** (1) tạo client. (2) `chat.completions.create(model=deployment, messages=[system,user])`. (3) in `choices[0].message.content` + `usage`.
- **Thi nhớ:** `model` = tên **deployment** (không phải tên model); cần `api_version`.

### `02_chat_openai_sdk_responses_api.py`

- **Mục tiêu:** Gọi model qua **Responses API** (chuẩn mới agentic/multi-turn).
- **SDK:** `openai` (`client.responses.create`) trên Azure OpenAI; hoặc `AIProjectClient.get_openai_client()`. *Tiền nhiệm:* Chat Completions API & Assistants API cũ → hợp nhất về Responses.
- **ENV:** `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION` (bản hỗ trợ responses), deployment.
- **Các bước:** (1) `responses.create(model=..., input="...")`. (2) đọc `output_text`. (3) nêu khác biệt với chat.completions.
- **Thi nhớ:** Responses API là nền cho agent & chuỗi `previous_response_id` (xem lab 04/03).

### `03_chat_foundry_models_openai_v1.py`

> ♻️ Đã đổi tên từ `03_chat_foundry_models_inference_client.py` (vì bỏ `azure-ai-inference` đã retire 2026-08-26).

- **Mục tiêu:** Suy luận Foundry Models (catalog non-OpenAI) qua **OpenAI SDK /v1** — alternative so với endpoint Azure OpenAI ở file 01.
- **SDK:** `openai` (`OpenAI`, `chat.completions.create`, `embeddings.create`) trỏ endpoint Foundry /v1. *Tiền nhiệm:* `azure-ai-inference` (`ChatCompletionsClient`/`EmbeddingsClient`) **đã deprecated**.
- **ENV:** `FOUNDRY_MODELS_ENDPOINT` (`.../openai/v1/`), `FOUNDRY_MODELS_API_KEY` (hoặc keyless scope `https://ai.azure.com/.default`), `FOUNDRY_NON_OPENAI_MODEL`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`.
- **Các bước:** (1) `chat.completions.create(model=<foundry-model>)`. (2) `embeddings.create(...)` ra vector. (3) in độ dài vector.
- **Thi nhớ:** cùng OpenAI /v1 phục vụ cả chat lẫn embeddings; phân biệt endpoint Foundry Models vs Azure OpenAI thuần.

### `04_chat_streaming_and_structured_json_schema.py`

- **Mục tiêu:** Stream token real-time + ép đầu ra theo **JSON Schema** (`strict`).
- **SDK:** `openai` (`stream=True`; `response_format={"type":"json_schema", ...}` hoặc `responses.parse` với Pydantic).
- **ENV:** như lab 01.
- **Các bước:** (1) stream: lặp `for chunk in ...` in dần `delta.content`. (2) structured: định nghĩa schema `strict:true`, `additionalProperties:false`; parse JSON trả về. (3) validate bằng Pydantic.
- **Thi nhớ:** structured outputs cần `strict` + schema đóng; streaming trả delta.

### `05_chat_multimodal_vision_and_audio_input.py`

- **Mục tiêu:** Gửi input đa phương thức (ảnh+text, audio) cho model hỗ trợ.
- **SDK:** `openai` (content parts: `input_text`/`input_image`/`input_audio`, hoặc image_url base64).
- **ENV:** deployment multimodal (vd gpt-4o), + đường dẫn ảnh/audio mẫu.
- **Các bước:** (1) encode ảnh base64 → message content parts. (2) hỏi về ảnh. (3) (tuỳ) audio input. (4) lưu ý rủi ro prompt-injection trong ảnh.
- **Thi nhớ:** cấu trúc message multimodal; model nào hỗ trợ modality nào.

### `06_prompt_engineering_system_and_grounding.py`

- **Mục tiêu:** Kỹ thuật prompt: system message, few-shot, grounding, điều chỉnh tham số (temperature/top_p/max_tokens).
- **SDK:** `openai` (chat.completions / responses).
- **ENV:** `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_CHAT_DEPLOYMENT`.
- **Các bước:** (1) so sánh cùng câu hỏi với các system prompt khác nhau. (2) thêm few-shot examples. (3) chèn ground data vào context. (4) đổi temperature/top_p xem khác biệt.
- **Thi nhớ:** prompt engineering + tham số = cách "Optimize generative AI"; grounding giảm fabrication.

---

## 03 · build_and_deploy_agents

### `01_agent_foundry_service_prompt_agent.py`

- **Mục tiêu:** Tạo & chạy **Prompt Agent** server-managed trên Foundry Agent Service.
- **SDK:** `azure-ai-projects` (`AIProjectClient.agents.create_version(...)`, `get_openai_client().responses.create`). *Tiền nhiệm:* `azure-ai-agents` (gói riêng, `create_agent`) → đã gộp vào `azure-ai-projects` 2.x.
- **ENV:** `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL`.
- **Các bước:** (1) tạo agent version với `instructions` + `model`. (2) gọi agent qua Responses. (3) in trả lời. (4) xoá agent test.
- **Thi nhớ:** agent là tài nguyên server-managed; phân biệt với gọi model trực tiếp.

### `02_agent_with_function_calling_tools.py`

- **Mục tiêu:** Gắn custom Python function làm tool + vòng lặp gọi hàm + `require_approval`.
- **SDK:** `azure-ai-projects` agents + định nghĩa function tool (JSON schema).
- **ENV:** như trên.
- **Các bước:** (1) khai báo tool schema. (2) agent gọi tool → nhận `tool_call`. (3) chạy hàm Python thật, trả `tool_output`. (4) lặp tới khi có câu trả lời; (5) demo `require_approval`.
- **Thi nhớ:** vòng lặp tool-calling; cơ chế phê duyệt hành động nhạy cảm.

### `03_agent_with_code_interpreter_and_file_search.py`

- **Mục tiêu:** Dùng built-in tools: **Code Interpreter** (tính toán/biểu đồ) + **File Search** (tra file).
- **SDK:** `azure-ai-projects` agents (`CodeInterpreterTool`, `FileSearchTool`) + upload file/vector store.
- **ENV:** như trên + file mẫu (.csv/.pdf).
- **Các bước:** (1) upload file → vector store. (2) tạo agent gắn 2 tool. (3) hỏi câu cần tính + tra file. (4) lấy output/biểu đồ; (5) dọn file.
- **Thi nhớ:** built-in tools khác custom tool; file search cần vector store.

### `04_agent_with_mcp_and_a2a_tools.py`

- **Mục tiêu:** Kết nối agent tới **MCP server** và **A2A** (agent-to-agent)/remote endpoint.
- **SDK:** `azure-ai-projects` agents (`McpTool`) + cấu hình A2A.
- **ENV:** như trên + `MCP_SERVER_URL`.
- **Các bước:** (1) khai báo MCP tool trỏ tới server. (2) agent dùng tool từ MCP. (3) demo gọi agent khác (A2A). (4) phê duyệt tool MCP.
- **Thi nhớ:** MCP = chuẩn mở kết nối tool/data; A2A = giao tiếp giữa agent.

### `05_agent_framework_local_and_foundry_client.py`

- **Mục tiêu:** Dựng agent bằng **Microsoft Agent Framework** với `FoundryChatClient` và client local/OpenAI.
- **SDK:** `agent-framework-core` + `agent-framework-foundry` (`ChatAgent`, `FoundryChatClient`). *Tiền nhiệm:* **Semantic Kernel** + **AutoGen** hợp nhất thành Agent Framework.
- **ENV:** `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL` (hoặc OpenAI creds).
- **Các bước:** (1) tạo `ChatAgent(chat_client=FoundryChatClient(...), instructions=...)`. (2) `agent.run("...")`. (3) đổi sang client local/OpenAI để thấy cùng API.
- **Thi nhớ:** Agent Framework là lớp code-first; chạy nhiều provider chung 1 API.

### `06_deploy_hosted_agent_responses_host_server.py`

- **Mục tiêu:** Host agent Agent-Framework thành HTTP endpoint chuẩn Foundry (`/responses`) để deploy Hosted Agent.
- **SDK:** `agent-framework` (`ResponsesHostServer` / host app) + ASGI (uvicorn).
- **ENV:** như lab 05 + `PORT`.
- **Các bước:** (1) bọc agent bằng host server expose `/responses`. (2) chạy uvicorn. (3) test POST. (4) nêu cách deploy lên Foundry Hosted Agent.
- **Thi nhớ:** hosted agent nói "ngôn ngữ" Responses; đóng gói để triển khai.

### `07_agent_bing_grounding_tool.py`

- **Mục tiêu:** Agent dùng **Grounding with Bing / web search tool** để trả lời có dữ liệu web mới + citation.
- **SDK:** `azure-ai-projects` agents (Bing grounding connection/tool).
- **ENV:** `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL` + Bing connection trong project.
- **Các bước:** (1) tạo agent gắn Bing grounding tool. (2) hỏi câu cần thông tin mới. (3) in trả lời + nguồn web.
- **Thi nhớ:** grounding tool = tri thức ngoài; khác RAG nội bộ (AI Search).

### `08_agent_openapi_spec_tool.py`

- **Mục tiêu:** Gắn API ngoài vào agent bằng **OpenAPI spec tool** (agent tự gọi REST theo schema).
- **SDK:** `azure-ai-projects` agents (OpenAPI tool nạp từ file spec).
- **ENV:** `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL` + file OpenAPI (.json/.yaml).
- **Các bước:** (1) nạp OpenAPI spec. (2) tạo agent gắn tool. (3) hỏi → agent gọi API thật. (4) in kết quả.
- **Thi nhớ:** OpenAPI tool = tích hợp API có sẵn, không cần code wrapper; cần auth scheme trong spec.

### `09_agent_azure_functions_tool.py`

- **Mục tiêu:** Agent gọi **Azure Functions tool** (chạy logic serverless của bạn).
- **SDK:** `azure-ai-projects` agents (Azure Function tool qua storage queue input/output).
- **ENV:** `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL` + Azure Function + Storage queue.
- **Các bước:** (1) khai báo function tool (tên, input/output queue). (2) agent kích hoạt function. (3) nhận kết quả.
- **Thi nhớ:** khác custom function (in-process): Azure Functions tool chạy serverless, async qua queue.

---

## 04 · agent_conversation_management

### `01_conv_stateless_manual_message_history.py`

- **Mục tiêu:** Tự quản mảng `messages` phía client (stateless), tự cắt/nén khi vượt context.
- **SDK:** `openai` chat.completions. *Tiền nhiệm:* cách cơ bản nhất, chưa có state server.
- **Các bước:** (1) giữ list messages qua nhiều lượt. (2) append user/assistant. (3) khi dài → cắt/nén lịch sử. (4) in hội thoại.
- **Thi nhớ:** stateless = client giữ toàn bộ ngữ cảnh; tốn token khi dài.

### `02_conv_server_managed_threads_and_runs.py`

- **Mục tiêu:** State phía server qua Threads/Conversations + Runs của Foundry Agent Service.
- **SDK:** `azure-ai-projects` agents (conversations/threads, runs).
- **ENV:** `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL`.
- **Các bước:** (1) tạo thread/conversation. (2) thêm message. (3) create run → poll status. (4) đọc message mới. (5) xoá thread.
- **Thi nhớ:** server giữ lịch sử; vòng đời run (queued→in_progress→completed).

### `03_conv_responses_api_previous_response_id.py`

- **Mục tiêu:** Nối hội thoại liên tục bằng `previous_response_id`.
- **SDK:** `openai`/`AIProjectClient` Responses API.
- **Các bước:** (1) `responses.create(input=...)` lượt 1 → lấy `id`. (2) lượt 2 truyền `previous_response_id`. (3) kiểm chứng model nhớ ngữ cảnh.
- **Thi nhớ:** Responses chaining = state nhẹ phía server, không gửi lại toàn bộ lịch sử.

### `04_conv_agent_framework_thread_persistence.py`

- **Mục tiêu:** Dùng `AgentThread` / `get_new_thread()` + serialize/deserialize để lưu bền vững.
- **SDK:** `agent-framework-core` (`AgentThread`). *Tiền nhiệm:* ChatHistory của Semantic Kernel.
- **Các bước:** (1) tạo thread. (2) chạy vài lượt. (3) `serialize()` ra JSON/file. (4) load lại, chạy tiếp.
- **Thi nhớ:** thread tách khỏi agent; lưu/khôi phục state để resume.

### `05_conv_memory_store_and_context_compaction.py`

- **Mục tiêu:** Bộ nhớ dài hạn theo user (`FoundryMemoryProvider`/memory tool) + nén ngữ cảnh.
- **SDK:** `agent-framework` memory provider / `azure-ai-projects`.
- **Các bước:** (1) ghi "fact" người dùng vào memory. (2) phiên sau truy hồi memory. (3) demo compaction khi hội thoại dài.
- **Thi nhớ:** memory = kiến thức bền; compaction giảm token mà giữ ý chính.

---

## 05 · multi_agent_orchestration_patterns

> Dùng **Microsoft Agent Framework** (`agent-framework-core`: `ChatAgent` + `WorkflowBuilder`). *Tiền nhiệm:* AutoGen (orchestration) + Semantic Kernel (workflow) → hợp nhất.
> **ENV chung cả nhóm:** `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL` (hoặc OpenAI creds). Mỗi file tạo vài `ChatAgent` rồi ghép theo pattern.

### `01_orch_sequential_pipeline_workflow.py`

- **Mục tiêu:** Pipeline tuần tự Researcher → Writer → Reviewer.
- **SDK:** Workflow (`Executor`, `@handler`, `ctx.send_message()`, `WorkflowBuilder`).
- **Các bước:** (1) định nghĩa 3 executor. (2) nối tuần tự. (3) chạy, in output từng chặng.
- **Thi nhớ:** sequential = output bước này là input bước sau.

### `02_orch_concurrent_fan_out_fan_in.py`

- **Mục tiêu:** Chạy song song nhiều nhánh (fan-out) rồi tổng hợp (fan-in).
- **SDK/construct:** `WorkflowBuilder` nhiều edge từ 1 node (fan-out) + node tổng hợp (fan-in); hoặc `asyncio.gather` nhiều `agent.run`.
- **Các bước:** (1) fan-out tới N agent phân tích. (2) chờ tất cả. (3) aggregator gộp kết quả.
- **Thi nhớ:** concurrent giảm latency; cần bước tổng hợp.

### `03_orch_handoff_routing_agents.py`

- **Mục tiêu:** Chuyển giao (Handoff) giữa các agent chuyên gia theo intent.
- **SDK/construct:** handoff orchestration — agent điều phối trả quyền cho agent kế tiếp theo intent/ngữ cảnh.
- **Các bước:** (1) router/triage agent đọc yêu cầu. (2) handoff sang agent phù hợp. (3) agent đích trả lời.
- **Thi nhớ:** handoff = định tuyến động theo ngữ cảnh.

### `04_orch_supervisor_as_tool_pattern.py`

- **Mục tiêu:** Supervisor gọi agent con như **tool** qua `.as_tool()`.
- **SDK/construct:** `agent.as_tool()` biến agent con thành tool của supervisor `ChatAgent`.
- **Các bước:** (1) bọc agent con thành tool. (2) supervisor quyết định gọi tool nào. (3) tổng hợp.
- **Thi nhớ:** "agent-as-tool" cho supervisor kiểm soát tập trung.

### `05_orch_group_chat_reflection_loop.py`

- **Mục tiêu:** Group chat / vòng phản biện Generator ↔ Critic tới khi đạt tiêu chí.
- **SDK/construct:** workflow vòng lặp (edge quay lại) hoặc group-chat pattern giữa 2 `ChatAgent`.
- **Các bước:** (1) generator tạo bản nháp. (2) critic chấm/góp ý. (3) lặp tới khi đạt hoặc hết vòng.
- **Thi nhớ:** reflection nâng chất lượng; cần điều kiện dừng.

---

## 06 · rag_and_foundry_iq_grounding

### `01_rag_ai_search_vector_and_hybrid_query.py`

- **Mục tiêu:** Truy vấn Azure AI Search: vector + keyword (BM25) = **hybrid**.
- **SDK:** `azure-search-documents` (`SearchClient`, `VectorizedQuery`). *Tiền nhiệm:* **Azure Cognitive Search** (đổi tên).
- **ENV:** `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`, `AZURE_SEARCH_INDEX`.
- **Các bước:** (1) tạo embedding cho query. (2) `search(search_text=..., vector_queries=[...])`. (3) in kết quả + score.
- **Thi nhớ:** hybrid kết hợp semantic vector + từ khoá; cần field vector trong index.

### `02_rag_ai_search_semantic_ranker.py`

- **Mục tiêu:** Bật **Semantic Ranker** để rerank + lấy captions/answers.
- **SDK:** `azure-search-documents` (`query_type=SEMANTIC`, `semantic_configuration_name`).
- **Các bước:** (1) search với semantic config. (2) đọc `@search.reranker_score`, captions, answers.
- **Thi nhớ:** semantic ranker là L2 rerank; cần cấu hình semantic trên index.

### `03_rag_indexer_skillset_enrichment_ocr.py`

- **Mục tiêu:** Dựng ingestion: data source → **Indexer** → **Skillset** (OCR/layout/chunking/custom Web API) → index.
- **SDK:** `azure-search-documents.indexes` (`SearchIndexerClient`, `SearchIndexerSkillset`, built-in skills).
- **ENV:** search + `BLOB_CONNECTION_STRING`.
- **Các bước:** (1) tạo index + data source (blob). (2) skillset (OCR, Split, Embedding skill). (3) indexer map fields. (4) run + xem trạng thái.
- **Thi nhớ:** indexer tự động kéo dữ liệu; skillset = AI enrichment pipeline.

### `04_rag_foundry_iq_agentic_retrieval.py`

- **Mục tiêu:** Dùng **Foundry IQ** knowledge base cho **agentic retrieval** (query planning đa nguồn, permission-aware).
- **SDK:** `azure-search-documents` (knowledge base/agentic retrieval API). *Mới 2026.*
- **ENV:** `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_KNOWLEDGE_BASE`.
- **Các bước:** (1) tạo/khai báo knowledge base. (2) gọi retrieve với reasoning effort. (3) đọc câu trả lời có citation + activity log.
- **Thi nhớ:** Foundry IQ chạy trên AI Search; reasoning effort đổi cost/latency; minimal = chỉ semantic (không LLM).

### `05_rag_connect_retrieval_to_agent_workflow.py`

- **Mục tiêu:** Gắn tool truy xuất (Azure AI Search tool) vào agent/workflow có kiểm soát nguồn.
- **SDK:** `azure-ai-projects` agents + Azure AI Search tool / Foundry IQ tool.
- **Các bước:** (1) tạo agent gắn search tool trỏ index/KB. (2) hỏi → agent tự retrieve + trả lời có grounding. (3) in citations.
- **Thi nhớ:** nối retrieval vào agent = RAG agentic; kiểm soát nguồn & grounding.

---

## 07 · vision_language_and_speech

### `01_vision_image_analysis_captions_tags_ocr.py`

- **Mục tiêu:** Phân tích ảnh: CAPTION, DENSE_CAPTIONS, TAGS, READ (OCR).
- **SDK:** `azure-ai-vision-imageanalysis` (`ImageAnalysisClient`, `VisualFeatures`). *Tiền nhiệm:* `azure-cognitiveservices-vision-computervision` (Computer Vision 3.x).
- **ENV:** `VISION_ENDPOINT`, `VISION_API_KEY`.
- **Các bước:** (1) analyze với nhiều `VisualFeatures`. (2) in caption + confidence, tags, text OCR.
- **Thi nhớ:** Image Analysis 4.0 một call nhiều feature; READ thay OCR cũ.

### `02_vision_object_detection_and_smart_crops.py`

- **Mục tiêu:** OBJECTS, PEOPLE, SMART_CROPS.
- **SDK:** như trên (`VisualFeatures.OBJECTS/PEOPLE/SMART_CROPS`).
- **Các bước:** (1) analyze. (2) in bounding box objects/people. (3) in vùng smart crop theo aspect ratio.
- **Thi nhớ:** smart crop trả vùng quan tâm; bounding box toạ độ.

### `03_language_ner_pii_redaction_sentiment.py`

- **Mục tiêu:** NER, PII detection + redaction, sentiment + opinion mining.
- **SDK:** `azure-ai-textanalytics` (`TextAnalyticsClient`). *Tiền nhiệm:* Text Analytics cũ (gộp vào Language service).
- **ENV:** `LANGUAGE_ENDPOINT`, `LANGUAGE_API_KEY`.
- **Các bước:** (1) `recognize_entities`. (2) `recognize_pii_entities` → dùng `redacted_text`. (3) `analyze_sentiment(show_opinion_mining=True)`.
- **Thi nhớ:** PII trả text đã che; sentiment theo câu + opinion.

### `04_language_clu_intent_and_summarization.py`

- **Mục tiêu:** CLU (intent/entity) + summarization (extractive & abstractive).
- **SDK:** `azure-ai-language-conversations` (`ConversationAnalysisClient`) + `azure-ai-textanalytics` (`begin_extract_summary`/`begin_abstract_summary`). *Tiền nhiệm:* LUIS → CLU.
- **ENV:** `LANGUAGE_*`, `CLU_PROJECT_NAME`, `CLU_DEPLOYMENT_NAME`.
- **Các bước:** (1) CLU analyze_conversation → top intent + entities. (2) extractive summary. (3) abstractive summary.
- **Thi nhớ:** CLU thay LUIS; 2 kiểu summarization.

### `05_translator_text_and_document_translation.py`

- **Mục tiêu:** Dịch text nhanh + dịch document hàng loạt.
- **SDK:** `azure-ai-translation-text` (`TextTranslationClient`) + `azure-ai-translation-document` (`DocumentTranslationClient`).
- **ENV:** `TRANSLATOR_*`.
- **Các bước:** (1) translate text đa ngôn ngữ đích. (2) batch document từ blob (source→target container). (3) poll + in trạng thái.
- **Thi nhớ:** document translation là async (long-running), cần blob + SAS.

### `06_speech_stt_tts_and_ssml_synthesis.py`

- **Mục tiêu:** STT, TTS, tuỳ biến giọng bằng **SSML**.
- **SDK:** `azure-cognitiveservices-speech` (`SpeechRecognizer`, `SpeechSynthesizer`).
- **ENV:** `SPEECH_KEY`, `SPEECH_REGION`.
- **Các bước:** (1) STT từ file/mic. (2) TTS text→audio. (3) SSML chỉnh rate/pitch/break/voice.
- **Thi nhớ:** SSML điều khiển ngữ điệu; chọn neural voice.

### `07_speech_voice_live_realtime_agent_modality.py`

- **Mục tiêu:** Giọng nói thời gian thực (**Voice Live** / speech-to-speech) hoặc audio modality cho agent.
- **SDK:** `azure-ai-voicelive` — **SDK GA 1.0, async-only** (cài kèm `[aiohttp]`, dùng `asyncio`), kết nối websocket realtime. *Tiền nhiệm:* trước đây phải tự ghép `azure-cognitiveservices-speech` (STT) + LLM + TTS thủ công.
- **ENV:** `SPEECH_KEY`, `SPEECH_REGION` (hoặc `FOUNDRY_PROJECT_ENDPOINT` + keyless).
- **Các bước:** (1) `async with` mở phiên VoiceLive. (2) stream audio vào/ra (event-driven). (3) nối với agent trả lời bằng giọng.
- **Thi nhớ:** Voice Live hợp nhất STT+LLM+TTS realtime trong 1 SDK; code **bất đồng bộ** (async).

### `08_vision_image_generation_and_editing.py`

- **Mục tiêu:** Tạo ảnh từ text (text-to-image) + chỉnh sửa (inpainting/mask edit) — **skill bắt buộc của Computer vision**.
- **SDK:** `openai` (`client.images.generate` / `images.edit`) với model image (vd GPT-Image) trên Azure OpenAI/Foundry.
- **ENV:** `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION` + deployment model image.
- **Các bước:** (1) generate ảnh từ prompt. (2) edit bằng mask (inpainting). (3) lưu ra `assets/output/`.
- **Thi nhớ:** generation controls (size/quality/mask); phân biệt **tạo ảnh** vs **phân tích ảnh** (lab 07/01).

### `09_vision_video_generation_and_editing.py`

- **Mục tiêu:** Tạo video từ text/ảnh tham chiếu (text-to-video) + chỉnh sửa — **skill bắt buộc của Computer vision**.
- **SDK:** `openai` / Foundry video generation API (vd Sora on Foundry) — long-running job.
- **ENV:** `AZURE_OPENAI_ENDPOINT` hoặc `FOUNDRY_PROJECT_ENDPOINT` + deployment model video.
- **Các bước:** (1) submit job tạo video từ prompt. (2) poll tới khi xong. (3) tải video về `assets/output/`.
- **Thi nhớ:** video generation là **async (job)**; có reference media + editing controls.

---

## 08 · information_extraction

### `01_doc_intelligence_layout_and_tables.py`

- **Mục tiêu:** Trích layout: trang, đoạn, **bảng**, toạ độ.
- **SDK:** `azure-ai-documentintelligence` (`DocumentIntelligenceClient`, model `prebuilt-layout`). *Tiền nhiệm:* **Form Recognizer** (`azure-ai-formrecognizer`).
- **ENV:** `DOC_INTELLIGENCE_ENDPOINT`, `DOC_INTELLIGENCE_API_KEY`.
- **Các bước:** (1) `begin_analyze_document("prebuilt-layout", ...)`. (2) duyệt tables/cells + bounding regions. (3) in markdown/table.
- **Thi nhớ:** layout cho cấu trúc + bảng; đổi tên từ Form Recognizer.

### `02_doc_intelligence_prebuilt_invoice_and_id.py`

- **Mục tiêu:** Trích field chuẩn hoá + confidence từ `prebuilt-invoice` và `prebuilt-idDocument`.
- **SDK:** như trên.
- **Các bước:** (1) analyze invoice → fields (VendorName, Total…). (2) analyze ID → fields. (3) in giá trị + confidence.
- **Thi nhớ:** prebuilt model trả field có confidence; chọn đúng model id.

### `03_content_understanding_prebuilt_document_analyzer.py`

- **Mục tiêu:** **Azure Content Understanding** prebuilt analyzer trích tài liệu theo schema.
- **SDK:** `azure-ai-contentunderstanding` (`ContentUnderstandingClient`) — **GA 1.1.0** (API 2025-11-01). *Tiền nhiệm:* trước khi có SDK phải gọi **REST thủ công bằng `requests`** (đừng dùng lại cách đó).
- **ENV:** `CONTENT_UNDERSTANDING_ENDPOINT`, `CONTENT_UNDERSTANDING_API_KEY`.
- **Các bước:** (1) `begin_analyze` với analyzer `prebuilt-documentAnalyzer`. (2) poll long-running operation. (3) đọc fields theo schema.
- **Thi nhớ:** CU thống nhất doc/audio/video/image; dựa trên analyzer + schema.

### `04_content_understanding_audio_video_multimodal.py`

- **Mục tiêu:** CU phân tích audio/video: phiên âm, phân đoạn, diarization, tóm tắt.
- **SDK:** `azure-ai-contentunderstanding` (`ContentUnderstandingClient`, analyzer audio/video). *Tiền nhiệm:* REST thủ công bằng `requests`.
- **Các bước:** (1) submit file audio/video. (2) poll. (3) đọc transcript + speaker + segment + summary.
- **Thi nhớ:** CU đa phương thức là điểm mạnh so với DI (chỉ document).

### `05_content_understanding_custom_schema_analyzer.py`

- **Mục tiêu:** Tạo & chạy **custom analyzer** với schema riêng (`extract`/`generate`/`classify`) + grounding mẫu.
- **SDK:** `azure-ai-contentunderstanding` (`begin_create_analyzer` + `begin_analyze`). Cần agentic/`analyze_inline` → dùng beta 1.2.0b3 (`--prerelease=allow`). *Tiền nhiệm:* REST thủ công bằng `requests`.
- **Các bước:** (1) định nghĩa schema field + kiểu generation. (2) tạo analyzer. (3) analyze tài liệu thật. (4) đọc field; (5) xoá analyzer.
- **Thi nhớ:** phân biệt extract vs generate vs classify; custom schema theo nghiệp vụ.

---

## 09 · observability_and_tracing

> Phủ skill "Set up observability" + "Monitor model/agent" (nhóm *Plan & manage* 25–30% và *Optimize* 30–35%).

### `01_agent_tracing_opentelemetry.py`

- **Mục tiêu:** Bật tracing cho agent bằng OpenTelemetry, xuất trace/token/latency lên Application Insights.
- **SDK:** `azure-monitor-opentelemetry` (`configure_azure_monitor`) + tracing của `agent-framework`/`azure-ai-projects`.
- **ENV:** `APPLICATIONINSIGHTS_CONNECTION_STRING`, `FOUNDRY_PROJECT_ENDPOINT`.
- **Các bước:** (1) `configure_azure_monitor(...)`. (2) chạy agent có span. (3) xem trace (token, latency, tool calls).
- **Thi nhớ:** observability = tracing + token analytics + safety signals + latency breakdown.

### `02_agent_monitoring_and_online_evaluation.py`

- **Mục tiêu:** Giám sát agent đã deploy + đánh giá hành vi (online evaluation, error analysis).
- **SDK:** `azure-ai-evaluation` (evaluators) + Foundry monitoring.
- **ENV:** `FOUNDRY_PROJECT_ENDPOINT`, `APPLICATIONINSIGHTS_CONNECTION_STRING`.
- **Các bước:** (1) thu thập trace/response thật. (2) chạy evaluator (groundedness/safety). (3) báo cáo chỉ số + lỗi.
- **Thi nhớ:** "evaluate agent behavior + error analysis" là skill riêng; khác eval model offline.

---

## 10 · production_assistant_agent (mini-repo production)

> **Không phải lab rời** — là 1 repo con hoàn chỉnh để học best practices. Dùng **Microsoft Agent Framework**
> (`Agent` + `@tool`) theo mẫu **handoff orchestration**: `triage` phân loại intent → chuyển cho specialist.
> Mock/local, chạy offline; deploy Azure Container Apps (managed identity, keyless).

- **Cấu trúc:** `src/assistant/` (config, chat_client, specialists, router, app CLI, host `/responses`, tools/) ·
  `mock_api/` (FastAPI đặt phòng/log work) · `data/` (seed SQLite + internal_docs) · `tests/` (offline) ·
  `Dockerfile` + `deploy/`.
- **7 intent:** qa · chitchat · meetings (tool→mock API) · docs (retrieval local) · worklog (tool→mock API) ·
  web (OpenAI `web_search`) · sales (text2sql + chart, **chỉ cho phép SELECT**).
- **Best practices:** tách tool khỏi logic cốt lõi để unit test không cần LLM; keyless-first; cấu hình tập trung;
  provider đổi được (Foundry ↔ Azure OpenAI).
- **Chạy/test:** `uv run pytest 10_production_assistant_agent/tests` (8 test offline). Xem `10_production_assistant_agent/README.md`.

## Tài liệu ôn nhanh mỗi chương

- Mỗi chương `NN_*/` có **`_REVIEW.html`** (CSS chung `assets/review.css`): tóm tắt · cú pháp cần nhớ ·
  **dễ nhầm với service khác** · exam tips/bẫy. Chương 00 kèm **bảng built-in roles**; chương 01 kèm **bảng SKU/Deployment Types**.

## Checklist khi viết xong mỗi file

- [ ] Chạy được: `uv run <đường_dẫn_file>.py`.
- [ ] Comment tiếng Việt đầy đủ; import có chú thích + SDK tiền nhiệm.
- [ ] Standalone (không import file lab khác).
- [ ] Có xử lý lỗi + dọn tài nguyên test.
- [ ] Dùng SDK/API đúng theo Microsoft Learn 2026 (tra lại nếu API đổi).
