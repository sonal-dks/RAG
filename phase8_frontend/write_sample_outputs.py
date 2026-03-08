"""
Write sample Phase 8 UI output to phase8_frontend/output/.

Exercises the new API contract (send_query with active_fund and conversation_id)
and fetch_mutual_funds to demonstrate frontend–backend integration.

Run: python -m phase8_frontend.write_sample_outputs
"""

import json
from pathlib import Path

from phase8_frontend.api_client import send_query, fetch_mutual_funds
from phase8_frontend.config import get_sample_questions

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

SAMPLE_EXCHANGES = [
    {"query": "What is the expense ratio of Quant Small Cap Fund?"},
    {"query": "Hi"},
    {"query": "What is the NAV?"},
    {"query": "What is the NAV?", "active_fund": "Quant Mid Cap Fund"},
    {"query": "What is the P/E ratio?", "active_fund": "Quant Small Cap Fund"},
    {"query": "My PAN is ABCDE1234F"},
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    funds_result = fetch_mutual_funds()
    conversation = []
    for ex in SAMPLE_EXCHANGES:
        result = send_query(
            ex["query"],
            active_fund=ex.get("active_fund"),
            conversation_id="sample-conv-001",
        )
        conversation.append({
            "request": ex,
            "response": {
                "answer": result["answer"],
                "citations": result.get("citations", []),
                "conversation_id": result.get("conversation_id", ""),
                "error": result.get("error"),
            },
        })

    out = {
        "description": "Sample UI conversation: requests (with optional active_fund) and backend responses.",
        "mutual_funds_available": funds_result.get("funds", []),
        "mutual_funds_error": funds_result.get("error"),
        "sample_questions": get_sample_questions(seed=42),
        "conversation": conversation,
    }
    out_path = OUTPUT_DIR / "sample_ui_conversation.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote sample UI conversation ({len(conversation)} exchanges) -> {out_path}")


if __name__ == "__main__":
    main()
