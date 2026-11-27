"""Tạo SQLite sales.sqlite (schema + dữ liệu mẫu) cho tool phân tích bán hàng.

Chạy: uv run python 10_production_assistant_agent/data/seed_sales_db.py
Hàm seed(db_path) tách riêng để test bơm DB tạm.
"""

import sqlite3
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")   # in tiếng Việt an toàn trên Windows
except Exception:
    pass

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "sales.sqlite"

SCHEMA_SQL = """
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS products;
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL
);
CREATE TABLE sales (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    sold_at TEXT NOT NULL,   -- YYYY-MM-DD
    region TEXT NOT NULL
);
"""

PRODUCTS = [
    (1, "Laptop Pro", "Electronics", 1200.0),
    (2, "Wireless Mouse", "Accessories", 25.0),
    (3, "Mechanical Keyboard", "Accessories", 80.0),
    (4, "4K Monitor", "Electronics", 350.0),
    (5, "USB-C Hub", "Accessories", 45.0),
]

SALES = [
    (1, 1, 3, "2026-11-02", "North"),
    (2, 2, 20, "2026-11-03", "North"),
    (3, 4, 5, "2026-11-05", "South"),
    (4, 1, 2, "2026-11-08", "South"),
    (5, 3, 10, "2026-11-10", "Central"),
    (6, 5, 15, "2026-11-12", "North"),
    (7, 4, 4, "2026-11-15", "Central"),
    (8, 2, 30, "2026-11-18", "South"),
    (9, 1, 1, "2026-11-20", "Central"),
    (10, 3, 7, "2026-11-22", "North"),
]


def seed(db_path: str | Path = DEFAULT_DB_PATH) -> Path:
    """Tạo DB tại db_path (idempotent: drop rồi tạo lại), trả về đường dẫn."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_SQL)
        connection.executemany("INSERT INTO products VALUES (?,?,?,?)", PRODUCTS)
        connection.executemany("INSERT INTO sales VALUES (?,?,?,?,?)", SALES)
        connection.commit()
    finally:
        connection.close()
    return db_path


if __name__ == "__main__":
    path = seed()
    print(f"Đã tạo DB bán hàng: {path}")
