"""
DukaanAI — Database Schema (Phase 2)

Tables:
  customers        — shop customers
  products         — sellable products with authoritative price + stock
  product_aliases  — curated synonym table for reliable entity resolution
                      (multiple aliases -> one product_id; alias text that
                      maps to >1 product must be treated by the resolver as
                      "needs clarification", never guessed)
  orders           — one row per confirmed order
  order_items      — line items per order, price snapshotted at sale time
"""

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS customers (
        customer_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL,
        contact       TEXT,
        created_at    TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS products (
        product_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        name           TEXT NOT NULL UNIQUE,
        unit           TEXT NOT NULL DEFAULT 'piece',   -- piece, kg, dozen, litre, etc.
        unit_price     REAL NOT NULL CHECK (unit_price >= 0),
        current_stock  REAL NOT NULL DEFAULT 0 CHECK (current_stock >= 0),
        minimum_stock  REAL NOT NULL DEFAULT 0 CHECK (minimum_stock >= 0),
        category       TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS product_aliases (
        alias_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id   INTEGER NOT NULL,
        alias_text   TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
        order_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id   INTEGER NOT NULL,
        timestamp     TEXT NOT NULL DEFAULT (datetime('now')),
        status        TEXT NOT NULL DEFAULT 'confirmed',  -- confirmed, cancelled
        total_amount  REAL NOT NULL CHECK (total_amount >= 0),
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id           INTEGER NOT NULL,
        product_id         INTEGER NOT NULL,
        quantity            REAL NOT NULL CHECK (quantity > 0),
        unit_price_at_sale  REAL NOT NULL CHECK (unit_price_at_sale >= 0),
        line_total          REAL NOT NULL CHECK (line_total >= 0),
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """,
    # Indexes — support the lookups the tool layer will do most often
    "CREATE INDEX IF NOT EXISTS idx_alias_text ON product_aliases(alias_text);",
    "CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id);",
    "CREATE INDEX IF NOT EXISTS idx_items_product ON order_items(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);",
]


def create_all_tables(conn):
    """Run all CREATE TABLE / INDEX statements. Safe to call repeatedly."""
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    for statement in SCHEMA_STATEMENTS:
        cur.execute(statement)
    conn.commit()
