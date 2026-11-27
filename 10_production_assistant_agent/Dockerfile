# Image deploy trợ lý lên Azure Container Apps (hoặc bất kỳ nơi chạy container nào).
# Dùng uv để cài dependency từ pyproject.toml của module này.
FROM python:3.12-slim

# uv (trình quản lý gói nhanh) copy sẵn từ image chính thức.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Cài dependency trước (tận dụng layer cache) rồi mới copy source.
COPY pyproject.toml ./
RUN uv sync --no-dev

# Copy mã nguồn + dữ liệu mẫu.
COPY src ./src
COPY mock_api ./mock_api
COPY data ./data

ENV PYTHONPATH=/app/src
EXPOSE 8080

# Khởi động HTTP host /responses. (Mock API chạy riêng — xem README.)
CMD ["uv", "run", "uvicorn", "assistant.host:app", "--host", "0.0.0.0", "--port", "8080"]
