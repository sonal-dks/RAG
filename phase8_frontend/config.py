"""
Phase 8 — Frontend configuration.

Backend API URL and sample questions pool.
"""

import os
import random

BACKEND_URL = os.environ.get("RAG_BACKEND_URL", "http://localhost:8000")
QUERY_ENDPOINT = f"{BACKEND_URL.rstrip('/')}/query"
MUTUAL_FUNDS_ENDPOINT = f"{BACKEND_URL.rstrip('/')}/mutual-funds"
LAST_UPDATED_ENDPOINT = f"{BACKEND_URL.rstrip('/')}/last-updated"

SAMPLE_QUESTIONS_POOL = [
    "What is the expense ratio of Quant Small Cap Fund?",
    "What are the top holdings of Quant Mid Cap Fund?",
    "What is the minimum investment for Quant ELSS?",
    "Who manages Quant Flexi Cap Fund?",
    "What is the risk level of Quant Infrastructure Fund?",
    "Tell me about Quant Large Cap Fund.",
    "What is the NAV of Quant ELSS Tax Saver Fund?",
    "What is the fund size of Quant Small Cap Fund?",
    "What are the exit load rules for Quant Flexi Cap?",
    "What is the minimum SIP for Quant Aggressive Hybrid Fund?",
    "What sectors does Quant Mid Cap Fund invest in?",
    "What is the expense ratio of Quant ELSS?",
    "Who is the fund manager of Quant Large Cap Fund?",
    "What is the lock-in period for Quant ELSS Tax Saver Fund?",
    "What is the AUM of Quant Focused Fund?",
    "What are the tax implications for Quant Equity funds?",
    "What is the minimum investment for Quant Multi Cap Fund?",
    "Tell me about Quant ESG Integration Strategy Fund.",
    "What is the NAV of Quant Small Cap Fund?",
    "What are the top 5 holdings of Quant Infrastructure Fund?",
]

NUM_SAMPLE_QUESTIONS = 3


def get_sample_questions(seed=None):
    """Return NUM_SAMPLE_QUESTIONS random sample questions (different each time unless seed is set)."""
    pool = list(SAMPLE_QUESTIONS_POOL)
    if seed is not None:
        rng = random.Random(seed)
        rng.shuffle(pool)
    else:
        random.shuffle(pool)
    return pool[:NUM_SAMPLE_QUESTIONS]


QUICK_PROMPTS = SAMPLE_QUESTIONS_POOL[:5]
