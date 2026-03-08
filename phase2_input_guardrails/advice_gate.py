"""
Phase 2.3 — Advice / Comparison Gate.

Keyword triggers for investment advice and comparison requests.
Returns canned redirect with fund URL when triggered.
"""

from .config import CANNED_ADVICE_REDIRECT, DEFAULT_FUND_PAGE_URL

# Triggers from architecture: "should I invest", "which is better", "recommend",
# "best fund", "compare returns", "will it go up", etc.
ADVICE_COMPARISON_PHRASES = [
    "should i invest", "which is better", "better than", "recommend",
    "best fund", "compare returns", "will it go up", "good to invest",
    "worth investing", "which fund to", "recommendation", "compare funds",
    "lump sum or sip", "how much to invest", "good time to invest",
    "should i buy", "should i sell", "should i redeem", "should i switch",
]


def check_advice_or_comparison(query: str) -> tuple[bool, str | None]:
    """
    Check if query triggers the advice/comparison gate.

    Returns (True, canned_message) if triggered, else (False, None).
    Canned message uses DEFAULT_FUND_PAGE_URL for redirect.
    """
    if not query or not isinstance(query, str):
        return False, None

    lower = query.strip().lower()
    if not lower:
        return False, None

    for phrase in ADVICE_COMPARISON_PHRASES:
        if phrase in lower:
            msg = CANNED_ADVICE_REDIRECT.format(url=DEFAULT_FUND_PAGE_URL)
            return True, msg

    return False, None
