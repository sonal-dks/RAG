"""
Write sample Phase 3 outputs to phase3_query_processing/output/.

Run: python -m phase3_query_processing.write_sample_outputs
"""

import json
from pathlib import Path

from phase3_query_processing.pipeline import process_query

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

SAMPLE_QUERIES = [
    "What is the NAV of Quant Small Cap Fund?",
    "What is the expnse ratio of quant elss?",
    "List top holdings of Quant Mid Cap Fund",
    "Who manages Quant Infrastructure Fund?",
    "What is the expense ratio?",
    "Tell me about AUM and NAV of Quant Large Cap",
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for q in SAMPLE_QUERIES:
        result = process_query(q)
        results.append({"query": q, "result": result})
    out_path = OUTPUT_DIR / "sample_query_processing_results.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(results)} sample results → {out_path}")


if __name__ == "__main__":
    main()
