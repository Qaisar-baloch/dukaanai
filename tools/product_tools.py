"""
DukaanAI — product_tools (Phase 5)

Entity resolution rule (Rule 1 — no hallucinated products):
resolve_product() only ever returns products that exist in the DB.
It never invents or "best-guesses" a product. Three possible outcomes:
  - status "found"      -> exactly one match, safe to proceed
  - status "ambiguous"   -> more than one match, caller MUST ask the
                              user to clarify, never auto-pick one
  - status "not_found"   -> nothing matched, caller tells the user
                              the product isn't available

Matching strategy (simple and predictable, appropriate for a curated
alias table rather than free-form fuzzy NLP):
  1. Exact match against product_aliases.alias_text (case-insensitive)
  2. Exact match against products.name (case-insensitive)
  3. Substring match against products.name (case-insensitive) as a
     last resort — may return multiple candidates, which correctly
     triggers "ambiguous" rather than guessing.
"""

from database.db import get_connection


def get_product(product_id: int):
    if product_id is None:
        return None
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM products WHERE product_id = ?", (product_id,)
    ).fetchone()
    return dict(row) if row else None


def search_products(query: str) -> list:
    """Free-text substring search over product names. Used for browsing,
    not for authoritative resolution (see resolve_product)."""
    if not query or not query.strip():
        return []
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE lower(name) LIKE lower(?)",
        (f"%{query.strip()}%",),
    ).fetchall()
    return [dict(r) for r in rows]


def resolve_product(text: str) -> dict:
    """Resolve a natural-language product mention to a DB product.
    See module docstring for the three possible statuses."""
    if not text or not text.strip():
        return {"status": "not_found", "query": text, "candidates": []}

    query = text.strip().lower()
    conn = get_connection()

    # 1. Exact alias match
    alias_rows = conn.execute(
        """
        SELECT p.* FROM products p
        JOIN product_aliases a ON a.product_id = p.product_id
        WHERE lower(a.alias_text) = ?
        """,
        (query,),
    ).fetchall()
    if len(alias_rows) == 1:
        return {"status": "found", "product": dict(alias_rows[0])}
    if len(alias_rows) > 1:
        return {
            "status": "ambiguous",
            "query": text,
            "candidates": [dict(r) for r in alias_rows],
        }

    # 2. Exact product name match
    name_row = conn.execute(
        "SELECT * FROM products WHERE lower(name) = ?", (query,)
    ).fetchone()
    if name_row:
        return {"status": "found", "product": dict(name_row)}

    # 3. Substring fallback — may be ambiguous, never auto-picked
    substring_rows = conn.execute(
        "SELECT * FROM products WHERE lower(name) LIKE ?", (f"%{query}%",)
    ).fetchall()
    if len(substring_rows) == 1:
        return {"status": "found", "product": dict(substring_rows[0])}
    if len(substring_rows) > 1:
        return {
            "status": "ambiguous",
            "query": text,
            "candidates": [dict(r) for r in substring_rows],
        }

    return {"status": "not_found", "query": text, "candidates": []}
