"""
Write sample Phase 7 API outputs to phase7_backend/output/.

Calls run_rag for several messages (with and without active_fund) and saves
request/response JSON for manual verification.

Run: python -m phase7_backend.write_sample_outputs
"""

import json
from pathlib import Path

from phase7_backend.pipeline import run_rag

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

SAMPLE_QUERIES = [
    {"query": "What is the expense ratio of Quant Small Cap Fund?"},
    {"query": "Hi"},
    {"query": "My PAN is ABCDE1234F"},
    {"query": "Should I invest in Quant ELSS?"},
    {"query": "What is the NAV?"},
    {"query": "What is the NAV?", "active_fund": "Quant Mid Cap Fund"},
    {"query": "What are the top holdings of Quant Mid Cap Fund?"},
    {"query": "What is the P/E ratio?", "active_fund": "Quant Small Cap Fund"},
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for q in SAMPLE_QUERIES:
        out = run_rag(q["query"], active_fund=q.get("active_fund"))
        results.append({
            "request": q,
            "response": {
                "answer": out["answer"],
                "citations": out.get("citations", []),
            },
        })
    out_path = OUTPUT_DIR / "sample_api_responses.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(results)} sample API responses -> {out_path}")


if __name__ == "__main__":
    main()
