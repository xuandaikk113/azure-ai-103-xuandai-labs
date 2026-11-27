"""Tool phân tích dữ liệu bán hàng: text -> SQL -> truy vấn SQLite -> vẽ chart.

An toàn: CHỈ cho phép câu SELECT (chặn INSERT/UPDATE/DELETE/DROP…) vì SQL do LLM sinh ra
là nguồn KHÔNG tin cậy. Các hàm cốt lõi tách khỏi @tool để unit test không cần LLM.
"""

import re
import sqlite3
from pathlib import Path
from typing import Callable

import matplotlib
matplotlib.use("Agg")   # backend không cần màn hình (chạy trên server/CI)
import matplotlib.pyplot as plt

from agent_framework import tool

from ..config import get_settings

# Schema mô tả cho LLM (đủ để sinh SQL đúng, không cần đọc DB).
SALES_SCHEMA = """
Bảng products(id INTEGER, name TEXT, category TEXT, unit_price REAL)
Bảng sales(id INTEGER, product_id INTEGER, quantity INTEGER, sold_at TEXT /* YYYY-MM-DD */, region TEXT)
sales.product_id -> products.id
""".strip()

# Chỉ cho phép đúng 1 câu SELECT; chặn mọi từ khoá ghi/DDL.
_FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|replace|attach|pragma)\b", re.IGNORECASE)


def is_safe_select(sql: str) -> bool:
    """True nếu sql là MỘT câu SELECT đọc-dữ-liệu an toàn."""
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned.lower().startswith("select"):
        return False
    if ";" in cleaned:                       # chặn multi-statement
        return False
    if _FORBIDDEN.search(cleaned):           # chặn từ khoá ghi/DDL
        return False
    return True


def sql_from_question(question: str, generate: Callable[[str], str]) -> str:
    """Sinh SQL từ câu hỏi tiếng Việt bằng hàm generate(prompt)->str (LLM injectable).

    Tách generate ra ngoài để test bơm stub, không cần gọi model thật.
    """
    prompt = (
        "Bạn là trợ lý chuyển câu hỏi thành MỘT câu SQLite SELECT (chỉ đọc).\n"
        f"Schema:\n{SALES_SCHEMA}\n"
        f"Câu hỏi: {question}\n"
        "Chỉ trả về đúng câu SQL, không giải thích, không markdown."
    )
    sql = generate(prompt).strip()
    # Gỡ hàng rào ```sql nếu model lỡ bọc.
    sql = re.sub(r"^```(?:sql)?|```$", "", sql, flags=re.IGNORECASE).strip()
    return sql


def execute_select(db_path: str, sql: str) -> tuple[list[str], list[tuple]]:
    """Chạy câu SELECT đã kiểm tra an toàn, trả (tên cột, các dòng)."""
    if not is_safe_select(sql):
        raise ValueError(f"Từ chối SQL không an toàn (chỉ cho phép SELECT): {sql!r}")
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.execute(sql)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
    finally:
        connection.close()
    return columns, rows


def plot_result(columns: list[str], rows: list[tuple], output_path: str) -> str | None:
    """Vẽ bar chart từ kết quả 2 cột (nhãn, số) và lưu PNG. Trả đường dẫn hoặc None.

    # ponytail: chỉ vẽ khi đúng 2 cột (nhãn, số) — đủ cho đa số câu hỏi tổng hợp; đa cột thì bỏ qua.
    """
    if len(columns) != 2 or not rows:
        return None
    labels = [str(row[0]) for row in rows]
    try:
        values = [float(row[1]) for row in rows]
    except (TypeError, ValueError):
        return None   # cột thứ 2 không phải số -> không vẽ

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.bar(labels, values, color="#4aa3ff")
    axis.set_xlabel(columns[0])
    axis.set_ylabel(columns[1])
    axis.set_title(f"{columns[1]} theo {columns[0]}")
    figure.autofmt_xdate(rotation=30)
    figure.tight_layout()
    figure.savefig(output_path, dpi=120)
    plt.close(figure)
    return output_path


def _default_generate(prompt: str) -> str:
    """Generator SQL mặc định: gọi Azure OpenAI /v1 (dùng khi chạy thật qua @tool)."""
    from openai import OpenAI
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    settings = get_settings()
    if not settings.azure_openai_endpoint:
        raise RuntimeError("Cần AZURE_OPENAI_ENDPOINT để sinh SQL (hoặc bơm generate khi test).")
    api_key = settings.azure_openai_api_key or get_bearer_token_provider(
        DefaultAzureCredential(), "https://ai.azure.com/.default",
    )
    client = OpenAI(base_url=settings.azure_openai_endpoint.rstrip("/") + "/openai/v1/", api_key=api_key)
    response = client.responses.create(model=settings.azure_openai_chat_deployment, input=prompt)
    return response.output_text


@tool
def analyze_sales(question: str) -> str:
    """Phân tích dữ liệu bán hàng từ câu hỏi tiếng Việt (text2sql) + vẽ biểu đồ.

    Tham số:
      question: câu hỏi phân tích, vd 'doanh thu theo vùng tháng này'.
    """
    settings = get_settings()
    sql = sql_from_question(question, _default_generate)
    columns, rows = execute_select(settings.sales_db_path, sql)

    chart_path = plot_result(columns, rows, str(Path(settings.chart_output_dir) / "sales_chart.png"))

    preview = ", ".join(" | ".join(str(cell) for cell in row) for row in rows[:5])
    message = f"SQL: {sql}\nKết quả ({len(rows)} dòng): {preview}"
    if chart_path:
        message += f"\nĐã lưu biểu đồ: {chart_path}"
    return message
