"""
Phase 6.1 — Post-generation PII scan.

Run the same PII check on the LLM response; if PII detected, block with canned response.
"""

from phase2_input_guardrails.pii_detector import check_pii as _check_pii


def scan_pii(text: str) -> tuple[bool, str | None]:
    """
    Scan response text for PII using Phase 2's regex pipeline.

    Returns (detected: bool, kind: str | None). kind is e.g. 'pan', 'aadhaar' if detected.
    """
    if not text or not isinstance(text, str):
        return False, None
    result = _check_pii(text.strip())
    return result.detected, result.kind
