"""
Phase 5 — Response Generation (Runtime).

Single Groq LLM call per query; system prompt + Phase 4 context → raw response.
"""

from .pipeline import process_query

__all__ = ["process_query"]
