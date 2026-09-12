"""
DukaanAI — inventory_tools (Phase 5)

Rules enforced here:
- check_stock() is read-only and always re-queries the DB — never
  trust a stock number the LLM or an earlier turn remembered.
- deduct_stock() must only be called inside a transaction alongside
  order creation (see order_tools.create_order) — never called on its
  own from the orchestrator for a customer sale.
- find_alternatives() only returns real, in-stock products from the
  same category — never invents an alternative (Rule: alternatives
  must exist in the DB).
"""

from database.db import get_connection


def check_stock(product_id: int, quantity: float) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT current_stock FROM products WHERE product_id = ?", (product_id,)
    ).fetchone()
    if row is None:
        return {"status": "error", "message": "Product not found."}

    current_stock = row["current_stock"]
    sufficient = current_stock >= quantity
    return {
        "status": "ok",
        "sufficient": sufficient,
        "current_stock": current_stock,
        "requested": quantity,
        "shortfall": max(0, quantity - current_stock),
    }


def deduct_stock(conn, product_id: int, quantity: float) -> None:
    """
    Deduct stock as part of an existing transaction. `conn` must be a
    connection already inside a `with transaction(conn):` block owned
    by the caller (order_tools.create_order) — this function does not
    open its own transaction, by design, so it can't run standalone
    against a live order (Rule 6: atomic order execution).
    """
    conn.execute(
        "UPDATE products SET current_stock = current_stock - ? WHERE product_id = ?",
        (quantity, product_id),
    )


def add_stock(product_id: int, quantity: float) -> dict:
    """Restocking — a standalone, deliberate shopkeeper action, so it
    manages its own transaction (unlike deduct_stock)."""
    from database.db import transaction

    conn = get_connection()
    with transaction(conn):
        conn.execute(
            "UPDATE products SET current_stock = current_stock + ? WHERE product_id = ?",
            (quantity, product_id),
        )
    return get_product_stock(product_id)


def get_product_stock(product_id: int) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT product_id, name, current_stock, minimum_stock FROM products WHERE product_id = ?",
        (product_id,),
    ).fetchone()
    return dict(row) if row else {"status": "error", "message": "Product not found."}


def get_low_stock_products() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE current_stock <= minimum_stock ORDER BY name"
    ).fetchall()
    return [dict(r) for r in rows]


def find_alternatives(product_id: int, limit: int = 3) -> list:
    """Find other in-stock products in the same category as product_id.
    Only ever returns real DB rows — never a fabricated suggestion."""
    conn = get_connection()
    product = conn.execute(
        "SELECT category FROM products WHERE product_id = ?", (product_id,)
    ).fetchone()
    if not product or not product["category"]:
        return []

    rows = conn.execute(
        """
        SELECT * FROM products
        WHERE category = ? AND product_id != ? AND current_stock > 0
        ORDER BY current_stock DESC
        LIMIT ?
        """,
        (product["category"], product_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]
