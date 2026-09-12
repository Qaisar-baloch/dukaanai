"""
DukaanAI — pricing_tools (Phase 5)

Rule 2 (no hallucinated prices) lives here: calculate_order_total()
ALWAYS looks up unit_price from the products table itself. It never
accepts a price as an argument from the caller — there is no
parameter for it. This makes it structurally impossible for the LLM
(or a bug in the orchestrator) to inject a fabricated price, since
the function simply doesn't expose a way to pass one in.
"""

from database.db import get_connection


def calculate_order_total(items: list) -> dict:
    """
    items: list of {"product_id": int, "quantity": float}

    Returns a breakdown with each line's authoritative unit_price
    (from the DB) and line_total, plus the overall total. If any
    product_id doesn't exist, that line is flagged as an error rather
    than silently skipped or priced at zero.
    """
    conn = get_connection()
    breakdown = []
    total = 0.0
    has_error = False

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        row = conn.execute(
            "SELECT name, unit_price FROM products WHERE product_id = ?",
            (product_id,),
        ).fetchone()

        if row is None:
            has_error = True
            breakdown.append(
                {"product_id": product_id, "error": "Product not found."}
            )
            continue

        line_total = round(row["unit_price"] * quantity, 2)
        total += line_total
        breakdown.append(
            {
                "product_id": product_id,
                "name": row["name"],
                "unit_price": row["unit_price"],
                "quantity": quantity,
                "line_total": line_total,
            }
        )

    return {
        "status": "error" if has_error else "ok",
        "items": breakdown,
        "total": round(total, 2),
    }
