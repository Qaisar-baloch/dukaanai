"""
DukaanAI — order_tools (Phase 5)

Rule 5 (confirmation before transaction) and Rule 6 (atomic order
execution) are both enforced here:

- create_order() is the ONLY function that writes an order. It must
  only be called by the orchestrator AFTER the user has confirmed a
  shown summary — this module doesn't know or care about the chat
  flow, but it re-validates stock itself as a second safety net, in
  case stock changed between the summary being shown and confirmed.
- All writes (order row, order_items rows, stock deduction) happen
  inside one `transaction(conn)` block. If ANY line item has
  insufficient stock at commit time, the whole transaction is aborted
  and nothing is written — no partial orders.
"""

from database.db import get_connection, transaction
from tools.pricing_tools import calculate_order_total
from tools.inventory_tools import deduct_stock


def create_order(customer_id: int, items: list) -> dict:
    """
    items: list of {"product_id": int, "quantity": float}

    Returns:
      {"status": "ok", "order_id": ..., "total": ..., "items": [...]}
      or
      {"status": "insufficient_stock", "shortages": [...]}
      or
      {"status": "error", "message": "..."}
    """
    if not items:
        return {"status": "error", "message": "No items in order."}

    conn = get_connection()

    # Re-validate stock right before committing (Rule 5/6 safety net —
    # stock may have changed since the summary was first shown).
    shortages = []
    for item in items:
        row = conn.execute(
            "SELECT name, current_stock FROM products WHERE product_id = ?",
            (item["product_id"],),
        ).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"Product {item['product_id']} not found.",
            }
        if row["current_stock"] < item["quantity"]:
            shortages.append(
                {
                    "product_id": item["product_id"],
                    "name": row["name"],
                    "requested": item["quantity"],
                    "available": row["current_stock"],
                }
            )

    if shortages:
        return {"status": "insufficient_stock", "shortages": shortages}

    pricing = calculate_order_total(items)
    if pricing["status"] == "error":
        return {"status": "error", "message": "Pricing failed — check product IDs."}

    with transaction(conn):
        cur = conn.execute(
            "INSERT INTO orders (customer_id, status, total_amount) VALUES (?, 'confirmed', ?)",
            (customer_id, pricing["total"]),
        )
        order_id = cur.lastrowid

        for line in pricing["items"]:
            conn.execute(
                """
                INSERT INTO order_items
                    (order_id, product_id, quantity, unit_price_at_sale, line_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    line["product_id"],
                    line["quantity"],
                    line["unit_price"],
                    line["line_total"],
                ),
            )
            deduct_stock(conn, line["product_id"], line["quantity"])

    return {"status": "ok", "order_id": order_id, "total": pricing["total"], "items": pricing["items"]}


def get_order(order_id: int) -> dict:
    conn = get_connection()
    order = conn.execute(
        "SELECT * FROM orders WHERE order_id = ?", (order_id,)
    ).fetchone()
    if not order:
        return None

    items = conn.execute(
        """
        SELECT oi.*, p.name FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        WHERE oi.order_id = ?
        """,
        (order_id,),
    ).fetchall()

    result = dict(order)
    result["items"] = [dict(i) for i in items]
    return result


def get_order_history(customer_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM orders WHERE customer_id = ? ORDER BY timestamp DESC",
        (customer_id,),
    ).fetchall()
    return [dict(r) for r in rows]
