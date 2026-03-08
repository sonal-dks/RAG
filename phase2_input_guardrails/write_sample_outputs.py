"""
Write sample Phase 2 outputs to phase2_input_guardrails/output/.

Run: python -m phase2_input_guardrails.write_sample_outputs
"""

import json
from pathlib import Path

from phase2_input_guardrails.guardrail import process_query

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

SAMPLE_QUERIES = [
    "What is the NAV of Quant Small Cap Fund?",
    "Hi",
    "My PAN is ABCDE1234F",
    "Should I invest in Quant ELSS?",
    "What is the weather today?",
    "Compare Quant Small Cap and Quant Mid Cap returns",
    "What is the expense ratio of Quant Flexi Cap Fund?",
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for q in SAMPLE_QUERIES:
        result = process_query(q)
        results.append({"query": q, "result": result})
    out_path = OUTPUT_DIR / "sample_guardrail_results.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(results)} sample results → {out_path}")


if __name__ == "__main__":
    main()
