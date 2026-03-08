"""
Phase 3.2 — Fund Name Resolver.

Resolve query to a single canonical fund (name + URL) from the lookup table.
If no fund or multiple funds mentioned, return need_clarification or first match (v1: limit to one).
"""

from .config import FUND_LOOKUP


def resolve_fund(query: str) -> dict:
    """
    Resolve which fund the query is about.

    Returns:
      - If one fund identified: {"resolved": True, "fund_key": str, "canonical_name": str, "url": str}
      - If no fund mentioned: {"resolved": False, "fund_key": None, "canonical_name": None, "url": None}
      - If multiple matches (v1): first match wins: {"resolved": True, ...}
    """
    if not query or not isinstance(query, str):
        return {"resolved": False, "fund_key": None, "canonical_name": None, "url": None}

    text = query.strip().lower()
    if not text:
        return {"resolved": False, "fund_key": None, "canonical_name": None, "url": None}

    matches: list[dict] = []
    for fund in FUND_LOOKUP:
        # Check canonical name (e.g. "quant small cap fund direct plan growth")
        if fund["canonical_name"].lower() in text:
            matches.append(fund)
            continue
        # Check fund_key (e.g. "quant-small-cap-fund")
        if fund["fund_key"].replace("-", " ") in text or fund["fund_key"] in text:
            matches.append(fund)
            continue
        # Check aliases
        for alias in fund["aliases"]:
            if alias in text:
                matches.append(fund)
                break

    if not matches:
        return {"resolved": False, "fund_key": None, "canonical_name": None, "url": None}

    # v1: limit to one fund — take first match
    chosen = matches[0]
    return {
        "resolved": True,
        "fund_key": chosen["fund_key"],
        "canonical_name": chosen["canonical_name"],
        "url": chosen["url"],
    }
