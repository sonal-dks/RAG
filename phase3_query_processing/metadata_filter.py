"""
Phase 3.3 — Metadata Filter Construction.

Build pre-filter for vector search: fund_name and optional section.
"""

from .config import SECTION_KEYWORDS


def build_section_filter(query: str) -> str | None:
    """
    Infer optional section filter from query (e.g. "holdings" -> section = "holdings").

    Returns section key for metadata filter, or None if no clear section.
    """
    if not query or not isinstance(query, str):
        return None

    lower = query.strip().lower()
    if not lower:
        return None

    for keyword, section in SECTION_KEYWORDS.items():
        if keyword in lower:
            return section
    return None
