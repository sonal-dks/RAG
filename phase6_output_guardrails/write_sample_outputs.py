"""
Write sample Phase 6 outputs to phase6_output_guardrails/output/.

Runs several raw responses (as from Phase 5) through the output guardrail pipeline.
Run: python -m phase6_output_guardrails.write_sample_outputs
"""

import json
from pathlib import Path

from phase6_output_guardrails import process_query
from phase6_output_guardrails.config import ALLOWED_URLS

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

SAMPLE_RAW_RESPONSES = [
    {
        "raw_response": "The expense ratio of Quant Small Cap Fund Direct Plan is 0.77% (Direct). "
        "There is no exit load. Last updated from sources: https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
        "source_url": ALLOWED_URLS[0],
    },
    {
        "raw_response": "You should invest in this fund for better returns. Consider SIP.",
        "source_url": None,
    },
    {
        "raw_response": "Please update your PAN ABCDE1234F in the portal.",
        "source_url": None,
    },
    {
        "raw_response": "The fund follows a small cap strategy. Last updated from sources: https://wrong-url.com/fund",
        "source_url": ALLOWED_URLS[0],
    },
    {
        "raw_response": "NAV is published daily. Minimum investment is 500.",
        "source_url": ALLOWED_URLS[1],
    },
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for item in SAMPLE_RAW_RESPONSES:
        out = process_query(
            item["raw_response"],
            source_url=item.get("source_url"),
        )
        results.append({
            "input_raw_response": item["raw_response"][:200] + ("..." if len(item["raw_response"]) > 200 else ""),
            "source_url_passed": item.get("source_url"),
            "result": {
                "validated_response": out["validated_response"],
                "citation_url": out["citation_url"],
                "pii_detected": out["pii_detected"],
                "advice_detected": out["advice_detected"],
                "citation_corrected": out["citation_corrected"],
            },
        })
    out_path = OUTPUT_DIR / "sample_output_guardrail_results.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(results)} sample results → {out_path}")


if __name__ == "__main__":
    main()
