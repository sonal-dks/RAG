# Phase 5 — Output

This folder holds **sample outputs** of the Response Generation phase so you can manually verify how Phase 5 behaves.

- **`sample_response_generation.json`** — One or more example runs: `user_query`, `retrieved_context_preview`, Phase 5 result (`raw_response`, `model_used`, `api_called`). When `GROQ_API_KEY` is set in `.env`, this uses a real Groq API call; otherwise a placeholder response is written so you can see the output structure.

**Setup:** Copy `.env.example` to `.env` in the project root and add your Groq API key (get one at https://console.groq.com/). The app loads `.env` automatically.

Regenerate with:
```bash
python -m phase5_response_generation.write_sample_outputs
```
