# DukaanAI — System Architecture (Phase 1)

Phase 1 is a design phase, not a code phase — this file is that design,
saved to the repo so nothing from Phase 1 is missing from the project.

## Overview

```
USER (Streamlit chat UI)
      │
      ▼
AI ORCHESTRATOR (single controller loop)
      │  ├─ intent detection
      │  ├─ tool selection (LLM function-calling)
      │  └─ pending-order state read/write
      ▼
BUSINESS TOOL LAYER (plain Python functions, no LLM inside)
      │  ├─ customer_tools
      │  ├─ product_tools (incl. alias resolution)
      │  ├─ inventory_tools
      │  ├─ pricing_tools
      │  ├─ order_tools
      │  └─ analytics_tools
      ▼
DATABASE (SQLite)
      │  ├─ customers
      │  ├─ products
      │  ├─ product_aliases
      │  ├─ orders
      │  └─ order_items
      ▲
      │
DASHBOARD (Streamlit page, reads via analytics_tools — bypasses orchestrator)
```

## Key architectural rules
- The LLM interprets language and selects tools. It never computes a
  price, invents a product, or asserts stock — those come from the DB.
- The LLM never executes SQL directly. All DB writes go through
  `tools/*` functions.
- Order creation always requires an explicit confirmation step before
  any stock is deducted or any row is written.
- The pending order lives in Streamlit's `st.session_state`, not the
  database, until the customer confirms it.
- The dashboard reads `tools/analytics_tools` directly — it does not
  route through the LLM, since KPI numbers should be exact and fast.

## Why this shape
- One orchestrator instead of a multi-agent framework: the workflow is
  a fixed sequence, not open-ended agent planning, so a framework like
  LangGraph/CrewAI would add complexity without adding reliability.
- Tool layer kept separate from the LLM so it can be fully unit-tested
  (see `tests/test_db.py`) without depending on the Groq API at all.

Full Phase 0 (requirements) and Phase 1 (this architecture) discussion,
including open decisions and their resolutions, is in the project chat
history — this file captures the final, approved shape.
