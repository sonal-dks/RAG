"""
Section-aware chunking of processed fund JSON for vector store.

Produces chunks with chunk_text, fund_name, source_url, section, scraped_at.
"""

import json
from pathlib import Path
from typing import Any


def _section_to_text(section_name: str, data: Any) -> str:
    """Convert a section (dict or list) to a short text block for embedding."""
    if data is None:
        return ""
    if isinstance(data, (str, int, float)):
        return f"{section_name}: {data}"
    if isinstance(data, list):
        parts = [f"{section_name}:"]
        for i, item in enumerate(data[:20]):  # limit list size
            if isinstance(item, dict):
                parts.append(json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        return " ".join(parts)
    if isinstance(data, dict):
        return f"{section_name}: " + json.dumps(data, ensure_ascii=False)
    return str(data)


def chunk_fund_document(fund_data: dict) -> list[dict]:
    """
    Chunk a single fund's processed JSON into sections.

    Each chunk has: chunk_text, fund_name, source_url, section, scraped_at.
    """
    fund_name = fund_data.get("fund_name") or fund_data.get("fund_key", "unknown")
    source_url = fund_data.get("source_url", "")
    scraped_at = fund_data.get("scraped_at", "")

    chunks: list[dict] = []
    section_keys = [
        "basic_info",
        "fund_category_and_risk",
        "performance_returns",
        "return_calculator",
        "holdings",
        "holding_analysis",
        "advanced_ratios",
        "minimum_investments",
        "returns_and_rankings",
        "exit_load",
        "tax_implication",
        "fund_managers",
        "about_fund",
        "fund_house",
        "other_plans_in_same_fund",
        "faqs",
    ]
    for key in section_keys:
        if key not in fund_data or fund_data[key] is None:
            continue
        text = _section_to_text(key, fund_data[key])
        if not text.strip():
            continue
        chunks.append({
            "chunk_text": text[:8000],  # cap single chunk size
            "fund_name": fund_name,
            "source_url": source_url,
            "section": key,
            "scraped_at": scraped_at,
        })
    return chunks
