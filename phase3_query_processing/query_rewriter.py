"""
Phase 3.1 — Query Rewriter.

Fix common typos, expand abbreviations, normalize fund name references.
"""

import re

from .config import ABBREVIATION_EXPANSIONS, FUND_LOOKUP, TYPO_CORRECTIONS


def rewrite_query(query: str) -> str:
    """
    Normalize the query: fix typos, expand abbreviations, optionally normalize fund names.

    Returns the rewritten query string.
    """
    if not query or not isinstance(query, str):
        return query

    text = query.strip()
    if not text:
        return text

    # Fix typos (word-boundary aware, case-insensitive)
    for wrong, correct in TYPO_CORRECTIONS.items():
        pattern = re.compile(r"\b" + re.escape(wrong) + r"\b", re.IGNORECASE)
        text = pattern.sub(correct, text)

    # Expand abbreviations: replace whole-word matches with expansion
    for abbr, expansion in ABBREVIATION_EXPANSIONS.items():
        pattern = re.compile(r"\b" + re.escape(abbr) + r"\b", re.IGNORECASE)
        text = pattern.sub(expansion, text)

    # Normalize fund name references: replace alias with canonical name in query
    lower = text.lower()
    for fund in FUND_LOOKUP:
        canonical = fund["canonical_name"]
        for alias in fund["aliases"]:
            # Prefer longer aliases first; match as whole phrase
            pattern = re.compile(r"\b" + re.escape(alias) + r"\b", re.IGNORECASE)
            if pattern.search(lower):
                text = pattern.sub(canonical, text)
                lower = text.lower()
                break  # one fund per alias match

    return text.strip()
