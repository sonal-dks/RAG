# Phase 8 — Output

This folder holds **sample UI output** for manual verification.

- **`sample_ui_conversation.json`** — Exercises the new API contract: queries with and without `active_fund`, the `GET /mutual-funds` response, and randomized sample questions. Demonstrates frontend–backend integration.

Regenerate with:
```bash
python -m phase8_frontend.write_sample_outputs
```

Ensure the Backend (Phase 7) is running, or the script will record error responses. Set `RAG_BACKEND_URL` if the API is not at `http://localhost:8000`.
