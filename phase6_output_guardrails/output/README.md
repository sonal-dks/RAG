# Phase 6 — Output

This folder holds **sample outputs** of the Output Guardrail & Formatting phase for manual verification.

- **`sample_output_guardrail_results.json`** — Example Phase 5 raw responses run through Phase 6: validated response, citation_url, and flags (pii_detected, advice_detected, citation_corrected).

Regenerate with:
```bash
python -m phase6_output_guardrails.write_sample_outputs
```
