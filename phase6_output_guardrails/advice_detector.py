"""
Phase 6.2 — Advice leak detection.

Scan for advisory language; if detected, replace with canned redirect response.
"""

import re
from typing import NamedTuple

from .config import (
    CANNED_ADVICE_RESPONSE_TEMPLATE,
    DEFAULT_FUND_PAGE_URL,
)


class AdviceScanResult(NamedTuple):
    detected: bool
    canned_response: str | None  # If detected, the replacement message


# Advisory phrases per architecture 6.2
_ADVICE_PATTERNS = [
    r"\byou\s+should\b",
    r"\bI\s+recommend\b",
    r"\binvest\s+in\b",
    r"\bbetter\s+returns?\b",
    r"\byou\s+must\b",
    r"\bit\s+is\s+better\s+to\b",
    r"\bconsider\s+investing\b",
    r"\bgood\s+to\s+invest\b",
    r"\badvise\s+(you\s+)?to\b",
    r"\bsuggest\s+(you\s+)?(to\s+)?invest\b",
    r"\bcompare\s+(returns?|performance)\b",
    r"\bhigher\s+returns?\b",
    r"\boutperform",
    r"\bportfolio\s+(allocation|suggestion)",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _ADVICE_PATTERNS]


def scan_advice(text: str, redirect_url: str | None = None) -> AdviceScanResult:
    """
    Scan for advisory language. If detected, return canned redirect response.

    redirect_url: if provided and allowed, use for the link; else use default.
    """
    if not text or not isinstance(text, str):
        return AdviceScanResult(False, None)
    t = text.strip()
    if not t:
        return AdviceScanResult(False, None)
    for pat in _COMPILED:
        if pat.search(t):
            url = redirect_url or DEFAULT_FUND_PAGE_URL
            return AdviceScanResult(True, CANNED_ADVICE_RESPONSE_TEMPLATE.format(url=url))
    return AdviceScanResult(False, None)
