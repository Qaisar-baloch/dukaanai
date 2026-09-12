"""
DukaanAI — Orchestrator (Phase 7 stub)

Owns the conversation loop. This is the ONLY module that should call
the LLM. It reads/writes pending-order state (passed in from Streamlit's
st.session_state by the UI layer — this module stays framework-agnostic)
and calls into tools/* for anything authoritative (price, stock, orders).

Architectural rule (non-negotiable, per approved Phase 0/1):
  - The LLM interprets language and selects tools.
  - The LLM NEVER computes a price, invents a product, or asserts stock.
  - The LLM NEVER executes SQL directly.

To implement in Phase 6/7:
  - parse_order(message: str) -> dict            (order understanding)
  - handle_message(message: str, pending_order: dict | None) -> dict
        returns: {"reply": str, "pending_order": dict | None}
"""
