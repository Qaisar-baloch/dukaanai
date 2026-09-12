"""
DukaanAI — Streamlit entry point.

Runs now (Phase 2/4 checkpoint): initializes the DB, seeds demo data,
and shows a placeholder page confirming the data layer is alive.
Chat + dashboard pages get built out in later phases.
"""

import streamlit as st
from database.seed import seed_all

st.set_page_config(page_title="DukaanAI", page_icon="🛒")

st.title("🛒 DukaanAI")
st.caption("From Customer Message to Business Action.")

conn = seed_all()

st.success("Database initialized and seeded.")

products = conn.execute(
    "SELECT name, unit, unit_price, current_stock, minimum_stock FROM products"
).fetchall()

st.subheader("Seeded products")
st.table(
    [
        {
            "Product": p["name"],
            "Unit": p["unit"],
            "Price": p["unit_price"],
            "Stock": p["current_stock"],
            "Min stock": p["minimum_stock"],
        }
        for p in products
    ]
)

st.info(
    "Chat assistant and dashboard are not implemented yet — "
    "this page just verifies Phase 2/4 (schema + seed data) end-to-end."
)
