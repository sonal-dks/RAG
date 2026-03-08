# Phase 7 — Output

This folder holds **sample API request/response** outputs for manual verification.

- **`sample_api_responses.json`** — Example requests (message) and the API response (response, citation_url) as returned by POST /query (or run_rag). Covers guardrail blocks (PII, advice), no fund specified, and optionally a full RAG response if the index is built and GROQ_API_KEY is set.

Regenerate with:
```bash
python -m phase7_backend.write_sample_outputs
```

To hit the real pipeline (retrieval + LLM), ensure ChromaDB is populated (`python -m phase4_retrieval_engine.pipeline` build_index_from_processed_dir) and `GROQ_API_KEY` is set in `.env`.
