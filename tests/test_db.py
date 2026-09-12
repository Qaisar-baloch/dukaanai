"""
DukaanAI — Phase 4 sanity tests for the database layer.

Run with: python -m pytest tests/ -v
(or just: python tests/test_db.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import get_connection, transaction, init_db
from database.seed import seed_all


def test_schema_creates_tables():
    conn = init_db()
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    expected = {"customers", "products", "product_aliases", "orders", "order_items"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"


def test_seed_is_idempotent():
    conn = seed_all()
    count_after_first = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    seed_all()
    count_after_second = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    assert count_after_first == count_after_second, "Seeding twice created duplicates"


def test_alias_resolves_to_product():
    conn = seed_all()
    row = conn.execute(
        """
        SELECT p.name FROM products p
        JOIN product_aliases a ON a.product_id = p.product_id
        WHERE a.alias_text = ?
        """,
        ("coke",),
    ).fetchone()
    assert row is not None, "'coke' alias did not resolve to a product"
    assert row["name"] == "Coca-Cola 250ml"


def test_transaction_rolls_back_on_error():
    conn = get_connection()
    before = conn.execute("SELECT COUNT(*) AS c FROM customers").fetchone()["c"]
    try:
        with transaction(conn):
            conn.execute("INSERT INTO customers (name) VALUES ('RollbackTest')")
            raise RuntimeError("force rollback")
    except RuntimeError:
        pass
    after = conn.execute("SELECT COUNT(*) AS c FROM customers").fetchone()["c"]
    assert before == after, "Transaction did not roll back on error"


if __name__ == "__main__":
    test_schema_creates_tables()
    test_seed_is_idempotent()
    test_alias_resolves_to_product()
    test_transaction_rolls_back_on_error()
    print("All Phase 4 DB tests passed.")
