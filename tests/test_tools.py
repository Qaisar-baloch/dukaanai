"""
DukaanAI — Phase 5 tests for the business tool layer.

Run with: python -m pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import get_connection
from database.seed import seed_all
from tools import customer_tools, product_tools, inventory_tools, pricing_tools, order_tools, analytics_tools


def setup_module(module):
    """Fresh, seeded DB before this test file's tests run."""
    seed_all()


# ---------- customer_tools ----------

def test_find_customer_exact_match():
    ali = customer_tools.find_customer("Ali")
    assert ali is not None
    assert ali["name"] == "Ali"


def test_find_customer_no_match_returns_none():
    assert customer_tools.find_customer("Nobody Here") is None


def test_create_customer_requires_confirmation():
    result = customer_tools.create_customer("New Test Customer")
    assert result["status"] == "needs_confirmation"
    # confirm it was NOT created
    assert customer_tools.find_customer("New Test Customer") is None


def test_create_customer_with_confirmation():
    result = customer_tools.create_customer("New Test Customer", confirmed=True)
    assert result["status"] == "ok"
    assert customer_tools.find_customer("New Test Customer") is not None


# ---------- product_tools ----------

def test_resolve_product_found_via_alias():
    result = product_tools.resolve_product("coke")
    assert result["status"] == "found"
    assert result["product"]["name"] == "Coca-Cola 250ml"


def test_resolve_product_not_found():
    result = product_tools.resolve_product("nonexistent product xyz")
    assert result["status"] == "not_found"


def test_resolve_product_roman_urdu_alias():
    result = product_tools.resolve_product("doodh")
    assert result["status"] == "found"
    assert result["product"]["name"] == "Milk (1L)"


# ---------- inventory_tools ----------

def test_check_stock_sufficient():
    coke = product_tools.resolve_product("coke")["product"]
    result = inventory_tools.check_stock(coke["product_id"], 2)
    assert result["sufficient"] is True


def test_check_stock_insufficient():
    coke = product_tools.resolve_product("coke")["product"]
    result = inventory_tools.check_stock(coke["product_id"], 9999)
    assert result["sufficient"] is False
    assert result["shortfall"] > 0


def test_find_alternatives_returns_real_products():
    coke = product_tools.resolve_product("coke")["product"]
    alternatives = inventory_tools.find_alternatives(coke["product_id"])
    assert all(a["product_id"] != coke["product_id"] for a in alternatives)
    for a in alternatives:
        assert a["current_stock"] > 0


# ---------- pricing_tools ----------

def test_calculate_order_total_matches_db_price():
    coke = product_tools.resolve_product("coke")["product"]
    result = pricing_tools.calculate_order_total(
        [{"product_id": coke["product_id"], "quantity": 3}]
    )
    assert result["status"] == "ok"
    assert result["total"] == round(coke["unit_price"] * 3, 2)


# ---------- order_tools (the full flow) ----------

def test_create_order_deducts_stock_atomically():
    ali = customer_tools.find_customer("Ali")
    coke = product_tools.resolve_product("coke")["product"]
    stock_before = coke["current_stock"]

    result = order_tools.create_order(
        ali["customer_id"], [{"product_id": coke["product_id"], "quantity": 2}]
    )
    assert result["status"] == "ok"
    assert result["total"] == round(coke["unit_price"] * 2, 2)

    updated = product_tools.get_product(coke["product_id"])
    assert updated["current_stock"] == stock_before - 2


def test_create_order_blocks_on_insufficient_stock():
    ali = customer_tools.find_customer("Ali")
    coke = product_tools.get_product(
        product_tools.resolve_product("coke")["product"]["product_id"]
    )
    result = order_tools.create_order(
        ali["customer_id"],
        [{"product_id": coke["product_id"], "quantity": coke["current_stock"] + 100}],
    )
    assert result["status"] == "insufficient_stock"

    # confirm nothing was written — no partial order
    unchanged = product_tools.get_product(coke["product_id"])
    assert unchanged["current_stock"] == coke["current_stock"]


# ---------- analytics_tools ----------

def test_today_sales_reflects_created_order():
    sales = analytics_tools.get_today_sales()
    assert sales["order_count"] >= 1
    assert sales["total_sales"] > 0


def test_low_stock_detection():
    low_stock = inventory_tools.get_low_stock_products()
    for p in low_stock:
        assert p["current_stock"] <= p["minimum_stock"]


if __name__ == "__main__":
    setup_module(None)
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"PASSED: {name}")
    print("All Phase 5 tool tests passed.")
