"""
DukaanAI — Seed data (Phase 2/4)

Idempotent: safe to run multiple times, will not duplicate data.
Seeds a small believable shop's products (with alias/synonym coverage
for English / Urdu / Roman Urdu) and a couple of demo customers.
"""

from database.db import get_connection, transaction, init_db

PRODUCTS = [
    # name, unit, unit_price, current_stock, minimum_stock, category, aliases
    ("Coca-Cola 250ml", "piece", 60, 24, 10, "beverage",
     ["coke", "coca cola", "cola", "cold drink"]),
    ("Pepsi 250ml", "piece", 60, 30, 10, "beverage",
     ["pepsi", "pepsi cola"]),
    ("Biscuits (Family Pack)", "piece", 40, 15, 10, "snack",
     ["biscuit", "biscuits", "biskut"]),
    ("Atta (Flour)", "kg", 180, 40, 15, "grocery",
     ["atta", "flour"]),
    ("Eggs (Dozen)", "dozen", 320, 8, 5, "grocery",
     ["eggs", "anda", "andey"]),
    ("Milk (1L)", "litre", 210, 12, 8, "dairy",
     ["milk", "doodh"]),
]

CUSTOMERS = [
    ("Ali", None),
    ("Sara", None),
]


def _seed_products(conn):
    cur = conn.cursor()
    for name, unit, price, stock, min_stock, category, aliases in PRODUCTS:
        cur.execute(
            """
            INSERT INTO products (name, unit, unit_price, current_stock, minimum_stock, category)
            SELECT ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = ?)
            """,
            (name, unit, price, stock, min_stock, category, name),
        )
        product_id = cur.execute(
            "SELECT product_id FROM products WHERE name = ?", (name,)
        ).fetchone()["product_id"]

        for alias in aliases:
            cur.execute(
                """
                INSERT INTO product_aliases (product_id, alias_text)
                SELECT ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM product_aliases
                    WHERE product_id = ? AND alias_text = ?
                )
                """,
                (product_id, alias.lower(), product_id, alias.lower()),
            )


def _seed_customers(conn):
    cur = conn.cursor()
    for name, contact in CUSTOMERS:
        cur.execute(
            """
            INSERT INTO customers (name, contact)
            SELECT ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM customers WHERE name = ?)
            """,
            (name, contact, name),
        )


def seed_all():
    conn = init_db()
    with transaction(conn):
        _seed_products(conn)
        _seed_customers(conn)
    return conn


if __name__ == "__main__":
    seed_all()
    print("Seed data inserted (or already present).")
