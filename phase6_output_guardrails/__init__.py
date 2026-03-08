"""
Phase 6 — Output Guardrail & Formatting (Runtime).

Validates LLM output (PII, advice leak, citation) and formats for display.
"""

from .pipeline import process_query

__all__ = ["process_query"]
