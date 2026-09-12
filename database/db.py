"""
DukaanAI — Database connection layer (Phase 4)

Single place that owns the SQLite connection and gives the tool layer
a safe way to run atomic multi-statement transactions (needed for
Rule 6: order creation + stock deduction must succeed or fail together).
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "dukaanai.db"


def get_connection():
    """Return a new SQLite connection with sane defaults.

    check_same_thread=False is required because Streamlit can call
    into this from more than one internal thread; for the MVP's single
    demo session this is safe. Row factory returns dict-like rows.
    """
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def transaction(conn):
    """Wrap a block of DB writes in a single atomic transaction.

    Usage:
        with transaction(conn):
            conn.execute(...)
            conn.execute(...)

    On any exception, everything in the block is rolled back — this is
    what keeps order creation + stock deduction atomic (Rule 6).
    """
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db():
    """Create tables if they don't exist. Call once at app startup."""
    from database.schema import create_all_tables

    conn = get_connection()
    create_all_tables(conn)
    return conn
