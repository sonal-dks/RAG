"""
Phase 3 — Query Processing (Runtime).

Normalize and enrich the validated query for optimal retrieval.
Components: Query Rewriter, Fund Name Resolver, Metadata Filter.
"""

from .pipeline import process_query

__all__ = ["process_query"]
