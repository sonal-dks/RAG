# Phase 4 — Output

This folder holds **sample outputs** of the Retrieval Engine so you can see how Phase 4 behaves (chunking and retrieval).

- **`sample_chunks.json`** — Chunks produced from one fund’s processed JSON (Quant Small Cap Fund). Shows how section-aware chunking works: each chunk has `chunk_text`, `fund_name`, `source_url`, `section`, `scraped_at`.
- **`sample_retrieval_result.json`** — One retrieval run: query, retrieved chunks (with similarity), and the assembled `retrieved_context` string that would be sent to the LLM.

Regenerate with:
```bash
python -m phase4_retrieval_engine.write_sample_outputs
```

Note: Retrieval sample uses an in-memory index built from the same fund’s chunks so you can see the full flow without pre-populating the main ChromaDB.
