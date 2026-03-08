"""
Phase 6 — Output Guardrail & Formatting pipeline.

Runs: PII Scan (6.1) → Advice Detection (6.2) → Citation Validation (6.3) → Formatter (6.4).
Returns validated, formatted response safe to display.
"""

from .advice_detector import scan_advice
from .citation_validator import validate_citation
from .config import CANNED_PII_RESPONSE, DEFAULT_FUND_PAGE_URL
from .formatter import format_response
from .pii_scan import scan_pii


def process_query(
    raw_response: str,
    *,
    source_url: str | None = None,
) -> dict:
    """
    Validate and format Phase 5 raw response for display.

    Args:
        raw_response: LLM output from Phase 5.
        source_url: Optional URL from retrieval (used as fallback/citation if valid).

    Returns:
        - validated_response: str — safe to display (may be canned if PII/advice detected).
        - citation_url: str — whitelisted URL for "Last updated from sources".
        - pii_detected: bool
        - advice_detected: bool
        - citation_corrected: bool — True if URL was replaced (hallucination fix).
    """
    if not raw_response or not isinstance(raw_response, str):
        return {
            "validated_response": "",
            "citation_url": source_url or DEFAULT_FUND_PAGE_URL,
            "pii_detected": False,
            "advice_detected": False,
            "citation_corrected": False,
        }
    text = raw_response.strip()
    if not text:
        return {
            "validated_response": "",
            "citation_url": source_url or DEFAULT_FUND_PAGE_URL,
            "pii_detected": False,
            "advice_detected": False,
            "citation_corrected": False,
        }

    # 6.1 PII scan
    pii_detected, _ = scan_pii(text)
    if pii_detected:
        return {
            "validated_response": CANNED_PII_RESPONSE,
            "citation_url": source_url or DEFAULT_FUND_PAGE_URL,
            "pii_detected": True,
            "advice_detected": False,
            "citation_corrected": False,
        }

    # 6.2 Advice leak detection
    advice_result = scan_advice(text, redirect_url=source_url)
    if advice_result.detected and advice_result.canned_response:
        return {
            "validated_response": advice_result.canned_response,
            "citation_url": source_url or DEFAULT_FUND_PAGE_URL,
            "pii_detected": False,
            "advice_detected": True,
            "citation_corrected": False,
        }

    # 6.3 Citation validation
    fallback = source_url if source_url else DEFAULT_FUND_PAGE_URL
    cite_result = validate_citation(text, fallback_url=source_url)

    # 6.4 Format (5-sentence cap, append citation if missing)
    validated = format_response(cite_result.corrected_text, citation_url=cite_result.validated_url)

    return {
        "validated_response": validated,
        "citation_url": cite_result.validated_url or fallback,
        "pii_detected": False,
        "advice_detected": False,
        "citation_corrected": cite_result.was_corrected,
    }
