"""
Write sample Phase 5 outputs to phase5_response_generation/output/.

Runs one (or more) response generation with canned context. Uses real Groq API if
GROQ_API_KEY is set in .env; otherwise writes a placeholder.
Run: python -m phase5_response_generation.write_sample_outputs
"""

import json
import os
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent

from phase5_response_generation.pipeline import process_query
from phase5_response_generation.generator import _read_groq_key

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# Canned context (similar to Phase 4 output) for a factual query
SAMPLE_CONTEXT = """---
expense_ratio: 0.77% (Direct). The fund has no exit load.
Source: https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth
---
Quant Small Cap Fund Direct Plan Growth. Equity - Small Cap. Risk: Very High.
Source: https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth
---
"""

SAMPLE_QUERY = "What is the expense ratio of Quant Small Cap Fund?"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    has_key = bool(_read_groq_key())

    result = process_query(
        SAMPLE_QUERY,
        SAMPLE_CONTEXT,
        sufficient=True,
    )
    context_preview = SAMPLE_CONTEXT[:500] + "..." if len(SAMPLE_CONTEXT) > 500 else SAMPLE_CONTEXT
    output = {
        "user_query": SAMPLE_QUERY,
        "retrieved_context_preview": context_preview,
        "retrieved_context_length": len(SAMPLE_CONTEXT),
        "result": {
            "raw_response": result["raw_response"],
            "model_used": result["model_used"],
            "api_called": result["api_called"],
        },
        "note": "Real Groq API call." if has_key else "Placeholder (GROQ_API_KEY not set). Set it for a real response.",
    }
    out_path = OUTPUT_DIR / "sample_response_generation.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote sample response → {out_path}")
    if not has_key:
        print("Set GROQ_API_KEY in .env for a real LLM response, then re-run.")


if __name__ == "__main__":
    main()
