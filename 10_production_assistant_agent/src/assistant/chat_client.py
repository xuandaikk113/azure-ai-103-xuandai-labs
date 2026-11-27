"""Dựng ChatClient cho Agent Framework theo provider trong cấu hình.

Cùng một API Agent chạy được nhiều provider — chỉ đổi client ở đây:
  - FoundryChatClient : keyless qua DefaultAzureCredential (khuyến nghị trên Azure).
  - OpenAIChatClient  : Azure OpenAI /v1 (hoặc OpenAI thuần).
"""

from azure.identity import DefaultAzureCredential
from agent_framework.foundry import FoundryChatClient   # gói agent-framework-foundry

from .config import Settings


def build_chat_client(settings: Settings):
    """Trả về chat client phù hợp provider. Dùng chung cho mọi agent (triage + specialist)."""
    if settings.llm_provider == "openai":
        if not settings.azure_openai_endpoint:
            raise RuntimeError("Thiếu AZURE_OPENAI_ENDPOINT cho provider 'openai'.")
        # import tại chỗ: chỉ cần khi thực sự dùng provider openai.
        from agent_framework.openai import OpenAIChatClient
        # base_url trỏ /openai/v1/. api_key có thể bỏ nếu dùng keyless (token provider).
        return OpenAIChatClient(
            model=settings.azure_openai_chat_deployment,
            base_url=settings.azure_openai_endpoint.rstrip("/") + "/openai/v1/",
            api_key=settings.azure_openai_api_key,
        )

    # Mặc định: Foundry keyless (Entra ID) — AIProjectClient chỉ hỗ trợ Entra, không có key.
    if not settings.foundry_project_endpoint:
        raise RuntimeError("Thiếu FOUNDRY_PROJECT_ENDPOINT cho provider 'foundry'.")
    return FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=settings.foundry_model,
        credential=DefaultAzureCredential(),
    )
