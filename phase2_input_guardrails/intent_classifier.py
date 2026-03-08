"""
Phase 2.2 — Intent Classifier.

Classifies query into: factual_query, investment_advice, comparison_request,
greeting_chitchat, off_topic. Keyword and heuristic based (no LLM).
"""

import re
from typing import Literal

Intent = Literal[
    "factual_query",
    "investment_advice",
    "comparison_request",
    "greeting_chitchat",
    "off_topic",
]

# Greeting/chitchat triggers (lowercase)
GREETING_PATTERNS = [
    r"^\s*(hi|hello|hey|good\s*morning|good\s*afternoon|good\s*evening)\s*[!.]?\s*$",
    r"^\s*(how\s+are\s+you|what\'?s\s+up|howdy)\s*[!.]?\s*$",
    r"^\s*(thanks|thank\s+you|bye|goodbye)\s*[!.]?\s*$",
    r"^\s*(yes|no|ok|okay)\s*[!.]?\s*$",
]

# Off-topic: clearly not about Quant funds or mutual funds
OFF_TOPIC_KEYWORDS = [
    "weather", "cricket", "movie", "recipe", "sports", "political",
    "election", "news", "football", "bollywood", "stock price", "bitcoin",
    "crypto", "nft", "real estate", "gold price", "forex",
]

# Mutual fund / Quant / Groww / scheme terms that suggest on-topic
ON_TOPIC_KEYWORDS = [
    "quant", "groww", "mutual fund", "mf", "scheme", "nav", "aum",
    "expense ratio", "holdings", "fund manager", "exit load", "sip",
    "lumpsum", "elss", "small cap", "mid cap", "large cap", "direct",
    "growth", "idcw", "amc", "factsheet", "returns", "portfolio",
]


def classify_intent(query: str) -> Intent:
    """
    Classify user query into one of: factual_query, investment_advice,
    comparison_request, greeting_chitchat, off_topic.
    """
    if not query or not isinstance(query, str):
        return "off_topic"

    text = query.strip()
    if not text:
        return "off_topic"

    lower = text.lower()

    # Greeting/chitchat: short and matches greeting patterns
    if len(text.split()) <= 6:
        for pat in GREETING_PATTERNS:
            if re.match(pat, lower, re.IGNORECASE):
                return "greeting_chitchat"

    # Investment advice / comparison
    if _is_advice_or_comparison(lower):
        if _is_comparison(lower):
            return "comparison_request"
        return "investment_advice"

    # Off-topic: contains off-topic keywords and no on-topic keywords
    has_off = any(k in lower for k in OFF_TOPIC_KEYWORDS)
    has_on = any(k in lower for k in ON_TOPIC_KEYWORDS)
    if has_off and not has_on:
        return "off_topic"

    # Default: factual query (about funds, NAV, etc.)
    return "factual_query"


def _is_advice_or_comparison(lower: str) -> bool:
    advice_phrases = [
        "should i invest", "can i invest", "is it good to invest",
        "recommend", "recommendation", "best fund", "which fund",
        "which is better", "compare returns", "compare funds", "compare ",
        "will it go up", "should i buy", "should i sell", "should i redeem",
        "should i switch", "worth investing", "better than",
        "good time to invest", "lump sum or sip", "how much to invest",
    ]
    return any(p in lower for p in advice_phrases)


def _is_comparison(lower: str) -> bool:
    if "compare" in lower or "comparison" in lower:
        return True
    if "which is better" in lower or "better than" in lower:
        return True
    if " vs " in lower or " versus " in lower:
        return True
    if "difference between" in lower or "best among" in lower:
        return True
    if " and " in lower and ("quant" in lower or "fund" in lower):
        return True
    return False
