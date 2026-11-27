"""Test text2sql + chart — bơm SQL generator giả, không cần LLM."""

import sqlite3
from pathlib import Path

import pytest

from assistant.tools.sales_analytics import (
    is_safe_select, sql_from_question, execute_select, plot_result,
)


def _seed(db_path) -> None:
    connection = sqlite3.connect(db_path)
    connection.executescript("CREATE TABLE sales(id INTEGER, region TEXT, quantity INTEGER);")
    connection.executemany(
        "INSERT INTO sales VALUES (?,?,?)",
        [(1, "North", 10), (2, "South", 5), (3, "North", 7)],
    )
    connection.commit()
    connection.close()


def test_is_safe_select():
    assert is_safe_select("SELECT * FROM sales")
    assert not is_safe_select("DROP TABLE sales")
    assert not is_safe_select("SELECT 1; DELETE FROM sales")   # multi-statement
    assert not is_safe_select("UPDATE sales SET quantity=0")


def test_sql_from_question_strips_markdown_fence():
    stub = lambda prompt: "```sql\nSELECT region, SUM(quantity) FROM sales GROUP BY region\n```"
    sql = sql_from_question("tổng số lượng theo vùng", stub)
    assert sql.lower().startswith("select")
    assert "```" not in sql


def test_execute_and_plot(tmp_path):
    db_path = tmp_path / "sales.sqlite"
    _seed(db_path)
    columns, rows = execute_select(str(db_path), "SELECT region, SUM(quantity) FROM sales GROUP BY region")
    assert columns == ["region", "SUM(quantity)"]
    assert len(rows) == 2   # North, South
    output = plot_result(columns, rows, str(tmp_path / "chart.png"))
    assert output and Path(output).exists()


def test_execute_rejects_unsafe_sql(tmp_path):
    db_path = tmp_path / "sales.sqlite"
    _seed(db_path)
    with pytest.raises(ValueError):
        execute_select(str(db_path), "DELETE FROM sales")
