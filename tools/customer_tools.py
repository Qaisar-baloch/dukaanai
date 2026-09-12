"""
DukaanAI — customer_tools (Phase 5)

Rules enforced here:
- find_customer() never invents a match — exact case-insensitive name
  match only. If nothing matches, returns None; the caller (orchestrator)
  decides whether to offer creating a new customer.
- create_customer() requires an explicit `confirmed=True` flag. This
  mirrors the approved Phase 0 decision: customer creation on the fly
  is allowed, but only after the user has confirmed it — the tool
  itself refuses to create anything silently.
"""

from database.db import get_connection, transaction


def find_customer(name: str):
    """Exact, case-insensitive name match. No fuzzy guessing here."""
    if not name or not name.strip():
        return None
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM customers WHERE lower(name) = lower(?)", (name.strip(),)
    ).fetchone()
    return dict(row) if row else None


def get_customer(customer_id: int):
    if customer_id is None:
        return None
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    return dict(row) if row else None


def create_customer(name: str, contact: str = None, confirmed: bool = False) -> dict:
    """
    Create a new customer. Refuses unless confirmed=True was passed by
    the orchestrator, which should only happen after the user has
    explicitly agreed to create a new customer record.
    """
    if not name or not name.strip():
        return {"status": "error", "message": "Customer name is required."}
    if not confirmed:
        return {
            "status": "needs_confirmation",
            "message": f"Create new customer '{name}'? Confirm to proceed.",
        }

    existing = find_customer(name)
    if existing:
        return {"status": "ok", "customer": existing, "created": False}

    conn = get_connection()
    with transaction(conn):
        cur = conn.execute(
            "INSERT INTO customers (name, contact) VALUES (?, ?)", (name.strip(), contact)
        )
        customer_id = cur.lastrowid

    return {"status": "ok", "customer": get_customer(customer_id), "created": True}


def get_customer_order_history(customer_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT order_id, timestamp, status, total_amount
        FROM orders
        WHERE customer_id = ?
        ORDER BY timestamp DESC
        """,
        (customer_id,),
    ).fetchall()
    return [dict(r) for r in rows]
