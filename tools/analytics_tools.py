"""
DukaanAI — analytics_tools (Phase 5)

Read-only. Powers both the dashboard (called directly, no LLM
involved) and chat business-questions (LLM phrases these numbers,
never computes them itself).
"""

from database.db import get_connection


def get_today_sales() -> dict:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT COALESCE(SUM(total_amount), 0) AS total, COUNT(*) AS order_count
        FROM orders
        WHERE date(timestamp) = date('now') AND status = 'confirmed'
        """
    ).fetchone()
    return {"total_sales": row["total"], "order_count": row["order_count"]}


def get_total_sales() -> dict:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT COALESCE(SUM(total_amount), 0) AS total, COUNT(*) AS order_count
        FROM orders
        WHERE status = 'confirmed'
        """
    ).fetchone()
    return {"total_sales": row["total"], "order_count": row["order_count"]}


def get_sales_by_product() -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT p.name, SUM(oi.quantity) AS total_quantity, SUM(oi.line_total) AS total_revenue
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.status = 'confirmed'
        GROUP BY p.product_id
        ORDER BY total_revenue DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def get_best_sellers(limit: int = 5) -> list:
    return get_sales_by_product()[:limit]


def get_sales_by_day(days: int = 7) -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT date(timestamp) AS day, SUM(total_amount) AS total
        FROM orders
        WHERE status = 'confirmed' AND date(timestamp) >= date('now', ?)
        GROUP BY date(timestamp)
        ORDER BY day
        """,
        (f"-{days} days",),
    ).fetchall()
    return [dict(r) for r in rows]
