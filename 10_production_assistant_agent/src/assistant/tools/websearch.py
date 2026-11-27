"""Tool tìm kiếm internet — dùng web_search built-in của OpenAI Responses API.

Nếu chưa cấu hình endpoint (chạy offline), trả kết quả GIẢ LẬP có đánh dấu rõ ràng
để pipeline vẫn chạy được mà không gọi ra ngoài.
"""

from agent_framework import tool
from openai import OpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from ..config import get_settings


@tool
def search_web(query: str) -> str:
    """Tìm kiếm thông tin mới trên internet và trả lời kèm nguồn.

    Tham số:
      query: nội dung cần tìm trên web.
    """
    settings = get_settings()
    endpoint = settings.azure_openai_endpoint

    # Fallback offline: không có endpoint -> trả giả lập (đánh dấu MOCK rõ ràng).
    if not endpoint:
        return f"(MOCK web search — chưa cấu hình AZURE_OPENAI_ENDPOINT) Kết quả giả lập cho: {query!r}"

    # Keyless ưu tiên; nếu có api_key thì dùng key.
    if settings.azure_openai_api_key:
        api_key = settings.azure_openai_api_key
    else:
        api_key = get_bearer_token_provider(
            DefaultAzureCredential(), "https://ai.azure.com/.default",   # scope cho /openai/v1
        )

    client = OpenAI(base_url=endpoint.rstrip("/") + "/openai/v1/", api_key=api_key)
    response = client.responses.create(
        model=settings.azure_openai_chat_deployment,
        tools=[{"type": "web_search"}],   # built-in hosted tool, chạy server-side
        input=query,
    )
    return response.output_text
