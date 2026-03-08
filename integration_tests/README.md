# End-to-End Integration Tests (Phases 1–8)

These tests verify that all modules (Phase 2 through Phase 8) communicate correctly and the application works as a complete system per `architecture.md`.

## Scope

| Test file | What it covers |
|-----------|----------------|
| **test_e2e_pipeline.py** | Full pipeline via `run_rag()` (Phase 2 → 3 → 4 → 5 → 6): guardrail blocks (PII, advice, comparison, greeting), no-fund clarification, empty message, and full RAG path (factual query with citation). |
| **test_e2e_api.py** | Phase 7 API: `GET /health`, `POST /query`, `POST /chat`; same scenarios as pipeline; validation and response contract for Frontend. |
| **test_e2e_frontend_backend.py** | Phase 8 ↔ Phase 7 contract: API response shape consumable by Frontend; `send_message` return shape matches backend. |

## Prerequisites

- **Phase 1** processed data in `data/processed/` (e.g. `quant-*.json`) for full RAG path tests (retrieval + optional LLM).
- **ChromaDB** index is built automatically by the `chroma_index_built` fixture when running tests marked `e2e_slow`.
- **GROQ_API_KEY** in `.env` is optional; if missing, Phase 5 returns an insufficient/fallback message and tests still pass.

## Run

```bash
# All integration tests (including index build and full RAG path)
pytest integration_tests/ -v

# Exclude slow tests (no ChromaDB build, no full RAG path)
pytest integration_tests/ -v -m "not e2e_slow"
```

## Markers

- **e2e_slow**: Tests that build the ChromaDB index or depend on retrieval/LLM. Use `-m "not e2e_slow"` for a quick run.
