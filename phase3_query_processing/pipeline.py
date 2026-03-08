"""
Phase 3 — Query Processing pipeline.

Orchestrates: Query Rewriter (3.1) → Fund Resolver (3.2) → Metadata Filter (3.3).
Output: enriched query + target fund metadata for retrieval engine.
"""

from .config import CLARIFICATION_MESSAGE
from .fund_resolver import resolve_fund
from .metadata_filter import build_section_filter
from .query_rewriter import rewrite_query


def process_query(query: str) -> dict:
    """
    Process validated query (from Phase 2) through Phase 3.

    Returns dict with:
      - enriched_query: str (rewritten, normalized)
      - fund_resolved: bool
      - fund_key: str | None
      - canonical_name: str | None
      - url: str | None
      - section_filter: str | None (optional for vector search)
      - clarification_message: str | None (only when fund_resolved is False)
    """
    if not query or not isinstance(query, str):
        return {
            "enriched_query": "",
            "fund_resolved": False,
            "fund_key": None,
            "canonical_name": None,
            "url": None,
            "section_filter": None,
            "clarification_message": CLARIFICATION_MESSAGE,
        }

    text = query.strip()
    if not text:
        return {
            "enriched_query": "",
            "fund_resolved": False,
            "fund_key": None,
            "canonical_name": None,
            "url": None,
            "section_filter": None,
            "clarification_message": CLARIFICATION_MESSAGE,
        }

    # 3.1 Query Rewriter
    enriched_query = rewrite_query(text)

    # 3.2 Fund Name Resolver
    fund = resolve_fund(enriched_query)

    # 3.3 Metadata Filter (section)
    section_filter = build_section_filter(enriched_query)

    if fund["resolved"]:
        return {
            "enriched_query": enriched_query,
            "fund_resolved": True,
            "fund_key": fund["fund_key"],
            "canonical_name": fund["canonical_name"],
            "url": fund["url"],
            "section_filter": section_filter,
            "clarification_message": None,
        }

    return {
        "enriched_query": enriched_query,
        "fund_resolved": False,
        "fund_key": None,
        "canonical_name": None,
        "url": None,
        "section_filter": None,
        "clarification_message": CLARIFICATION_MESSAGE,
    }
