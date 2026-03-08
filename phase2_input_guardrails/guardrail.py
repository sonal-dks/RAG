"""
Phase 2 — Input Guardrail Layer (orchestrator).

Runs: PII Detector → Intent Classifier → Advice/Comparison Gate.
Returns either a pass-through (clean query + intent) or a block (canned response).
"""

from typing import TypedDict

from .advice_gate import check_advice_or_comparison
from .config import (
    CANNED_ADVICE_REDIRECT,
    CANNED_GREETING,
    CANNED_OFF_TOPIC,
    CANNED_PII,
    DEFAULT_FUND_PAGE_URL,
)
from .intent_classifier import Intent, classify_intent
from .pii_detector import check_pii


class GuardrailPass(TypedDict):
    pass_through: bool
    intent: str
    query: str
    canned_response: None


class GuardrailBlock(TypedDict):
    pass_through: bool
    reason: str
    canned_response: str
    intent: None
    query: None


def process_query(user_query: str) -> GuardrailPass | GuardrailBlock:
    """
    Process user query through Phase 2 guardrails.

    Order: 1) PII check, 2) Intent classification, 3) Advice/Comparison gate.

    Returns:
      - If blocked: dict with pass_through=False, reason=..., canned_response=...
      - If passed: dict with pass_through=True, intent=..., query=... (cleaned)
    """
    if not user_query or not isinstance(user_query, str):
        return {
            "pass_through": False,
            "reason": "off_topic",
            "canned_response": CANNED_OFF_TOPIC,
            "intent": None,
            "query": None,
        }

    text = user_query.strip()
    if not text:
        return {
            "pass_through": False,
            "reason": "off_topic",
            "canned_response": CANNED_OFF_TOPIC,
            "intent": None,
            "query": None,
        }

    # 2.1 PII Detector
    pii_result = check_pii(text)
    if pii_result.detected:
        return {
            "pass_through": False,
            "reason": "pii",
            "canned_response": CANNED_PII,
            "intent": None,
            "query": None,
        }

    # 2.2 Intent Classifier
    intent = classify_intent(text)

    if intent == "greeting_chitchat":
        return {
            "pass_through": False,
            "reason": "greeting_chitchat",
            "canned_response": CANNED_GREETING,
            "intent": None,
            "query": None,
        }

    if intent == "off_topic":
        return {
            "pass_through": False,
            "reason": "off_topic",
            "canned_response": CANNED_OFF_TOPIC,
            "intent": None,
            "query": None,
        }

    if intent == "investment_advice":
        msg = CANNED_ADVICE_REDIRECT.format(url=DEFAULT_FUND_PAGE_URL)
        return {
            "pass_through": False,
            "reason": "investment_advice",
            "canned_response": msg,
            "intent": None,
            "query": None,
        }

    if intent == "comparison_request":
        msg = CANNED_ADVICE_REDIRECT.format(url=DEFAULT_FUND_PAGE_URL)
        return {
            "pass_through": False,
            "reason": "comparison_request",
            "canned_response": msg,
            "intent": None,
            "query": None,
        }

    # 2.3 Advice/Comparison Gate (double-check for borderline)
    triggered, canned = check_advice_or_comparison(text)
    if triggered and canned:
        return {
            "pass_through": False,
            "reason": "investment_advice",
            "canned_response": canned,
            "intent": None,
            "query": None,
        }

    # Pass through: factual_query
    return {
        "pass_through": True,
        "intent": "factual_query",
        "query": text,
        "canned_response": None,
    }
