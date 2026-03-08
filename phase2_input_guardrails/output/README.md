# Phase 2 — Output

This folder holds **sample outputs** of the Input Guardrail Layer so you can see how Phase 2 behaves.

- **`sample_guardrail_results.json`** — Example user queries and the Phase 2 result for each (pass-through vs block, reason, canned_response, or intent + query).

Regenerate with:
```bash
python -m phase2_input_guardrails.write_sample_outputs
```
