"""
Phase 2 — Input Guardrail Layer (Runtime).

Intercepts and classifies every user query before it reaches the retrieval engine.
Components: PII Detector, Intent Classifier, Advice/Comparison Gate.
"""

from .guardrail import process_query

__all__ = ["process_query"]
