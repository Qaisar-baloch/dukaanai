# DukaanAI

From Customer Message to Business Action.

AI-powered business assistant for micro-businesses. Shopkeepers manage
orders, inventory, and customers in natural language (English / Urdu /
Roman Urdu). See `docs/` (or the hackathon deck) for the full product
brief.

## Status

Phase 2 (database design) and Phase 4 (database implementation, partial)
are done and tested. Phase 5 (business tools), Phase 6 (order
understanding), and Phase 7 (orchestrator) are stubbed — see the
docstring in each file under `tools/` and `agents/orchestrator.py`.

## Project structure

```
dukaanai/
├── app.py                 # Streamlit entry point
├── requirements.txt
├── .env.example
├── database/
│   ├── db.py              # connection + transaction helper
│   ├── schema.py           # CREATE TABLE statements (Phase 2)
│   └── seed.py             # demo seed data, idempotent
├── tools/                  # Phase 5 — business logic, LLM-free
├── agents/
│   └── orchestrator.py     # Phase 7 — the only module allowed to call the LLM
├── tests/
│   └── test_db.py          # Phase 4 sanity tests
├── models/  services/  ui/  utils/   # reserved for later phases
```

## Local setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then add your real GROQ_API_KEY
```

## Run the tests

```bash
python -m pytest tests/ -v
```

## Run the app locally

```bash
streamlit run app.py
```

This currently seeds the DB and shows the product table as a checkpoint.
Chat and dashboard pages arrive in later phases.

## Deployment

See the note at the end of this conversation for the recommended
build → test → deploy path (short version: build and test locally, no
GPU/Colab needed since this project has no local model training —
Groq is a hosted API call — then push to GitHub and connect Streamlit
Cloud to the repo).
