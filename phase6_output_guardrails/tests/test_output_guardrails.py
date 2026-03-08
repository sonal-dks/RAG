"""
Phase 6 unit and acceptance tests.
"""

import pytest

from phase6_output_guardrails import process_query
from phase6_output_guardrails.advice_detector import scan_advice
from phase6_output_guardrails.citation_validator import validate_citation
from phase6_output_guardrails.config import (
    ALLOWED_URLS,
    CANNED_PII_RESPONSE,
    CITATION_PREFIX,
    DEFAULT_FUND_PAGE_URL,
    MAX_SENTENCES,
)
from phase6_output_guardrails.formatter import format_response
from phase6_output_guardrails.pii_scan import scan_pii


# --- Unit: pii_scan ---


def test_pii_scan_clean_text():
    detected, kind = scan_pii("The expense ratio is 0.77%.")
    assert detected is False
    assert kind is None


def test_pii_scan_pan_detected():
    detected, kind = scan_pii("My PAN is ABCDE1234F for KYC.")
    assert detected is True
    assert kind == "pan"


def test_pii_scan_empty():
    detected, kind = scan_pii("")
    assert detected is False


# --- Unit: advice_detector ---


def test_advice_scan_clean():
    result = scan_advice("The fund has an expense ratio of 0.5%.")
    assert result.detected is False
    assert result.canned_response is None


def test_advice_scan_you_should():
    result = scan_advice("You should invest in this fund for better returns.")
    assert result.detected is True
    assert result.canned_response is not None
    assert "investment advice" in result.canned_response.lower() or "unable" in result.canned_response.lower()
    assert "groww.in" in result.canned_response


def test_advice_scan_i_recommend():
    result = scan_advice("I recommend this scheme.")
    assert result.detected is True


def test_advice_scan_redirect_url_used():
    custom_url = "https://groww.in/mutual-funds/quant-elss-tax-saver-fund-direct-growth"
    result = scan_advice("You should invest here.", redirect_url=custom_url)
    assert result.detected is True
    assert custom_url in result.canned_response


# --- Unit: citation_validator ---


def test_citation_valid_url_preserved():
    good_url = "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"
    text = f"The NAV is 100. {CITATION_PREFIX} {good_url}"
    r = validate_citation(text, fallback_url=good_url)
    assert r.validated_url == good_url
    assert r.was_corrected is False
    assert good_url in r.corrected_text


def test_citation_hallucinated_url_replaced():
    bad_url = "https://evil.com/fund"
    fallback = ALLOWED_URLS[0]
    text = f"Answer here. {CITATION_PREFIX} {bad_url}"
    r = validate_citation(text, fallback_url=fallback)
    assert r.validated_url == fallback
    assert r.was_corrected is True
    assert fallback in r.corrected_text
    assert bad_url not in r.corrected_text or "evil" not in r.corrected_text.lower()


def test_citation_no_url_appends_fallback():
    text = "The expense ratio is 0.77%."
    fallback = ALLOWED_URLS[0]
    r = validate_citation(text, fallback_url=fallback)
    assert r.validated_url == fallback
    assert CITATION_PREFIX in r.corrected_text
    assert fallback in r.corrected_text


# --- Unit: formatter ---


def test_formatter_under_five_sentences_unchanged():
    text = "First. Second. Third."
    out = format_response(text, citation_url="https://groww.in/x")
    assert "First" in out
    assert CITATION_PREFIX in out
    assert "https://groww.in/x" in out


def test_formatter_over_five_sentences_truncated():
    text = "One. Two. Three. Four. Five. Six. Seven."
    out = format_response(text, citation_url=None)
    sentences = [s for s in out.split(". ") if s.strip()]
    assert len(sentences) <= MAX_SENTENCES


def test_formatter_max_sentences_constant():
    assert MAX_SENTENCES == 5


# --- Pipeline integration ---


def test_pipeline_clean_response():
    raw = "The expense ratio is 0.77%. Last updated from sources: https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"
    out = process_query(raw, source_url=ALLOWED_URLS[0])
    assert out["pii_detected"] is False
    assert out["advice_detected"] is False
    assert "expense ratio" in out["validated_response"].lower()
    assert "groww.in" in out["citation_url"]
    assert "validated_response" in out
    assert "citation_url" in out


def test_pipeline_pii_blocked():
    raw = "Your PAN ABCDE1234F is invalid."
    out = process_query(raw)
    assert out["pii_detected"] is True
    assert out["validated_response"] == CANNED_PII_RESPONSE
    assert "PAN" in CANNED_PII_RESPONSE or "personal" in CANNED_PII_RESPONSE.lower()


def test_pipeline_advice_replaced():
    raw = "You should invest in this fund for better returns."
    out = process_query(raw, source_url=ALLOWED_URLS[0])
    assert out["advice_detected"] is True
    assert "investment advice" in out["validated_response"].lower() or "unable" in out["validated_response"].lower()
    assert "groww.in" in out["validated_response"]


def test_pipeline_empty_input():
    out = process_query("")
    assert out["validated_response"] == ""
    assert out["citation_url"] == DEFAULT_FUND_PAGE_URL


def test_pipeline_none_input():
    out = process_query(None)
    assert out["validated_response"] == ""
    assert out["citation_url"] == DEFAULT_FUND_PAGE_URL


def test_pipeline_citation_corrected():
    bad = "https://wrong.com"
    raw = f"Fact. {CITATION_PREFIX} {bad}"
    out = process_query(raw, source_url=ALLOWED_URLS[0])
    assert out["citation_corrected"] is True
    assert ALLOWED_URLS[0] in out["validated_response"] or out["citation_url"] in ALLOWED_URLS


# --- Acceptance criteria ---


def test_ac1_output_has_required_keys():
    """AC1: Output has validated_response, citation_url, pii_detected, advice_detected, citation_corrected."""
    out = process_query("Some text.")
    assert "validated_response" in out
    assert "citation_url" in out
    assert "pii_detected" in out
    assert "advice_detected" in out
    assert "citation_corrected" in out
    assert isinstance(out["pii_detected"], bool)
    assert isinstance(out["advice_detected"], bool)
    assert isinstance(out["citation_corrected"], bool)


def test_ac2_pii_in_response_blocked():
    """AC2: If PII detected in raw response, return canned PII message."""
    out = process_query("Contact 9876543210 for support.")
    assert out["pii_detected"] is True
    assert out["validated_response"] == CANNED_PII_RESPONSE


def test_ac3_advice_leak_replaced():
    """AC3: If advice language detected, replace with canned redirect."""
    out = process_query("I recommend you invest in this fund.")
    assert out["advice_detected"] is True
    assert "groww.in" in out["validated_response"]
    assert "recommend" not in out["validated_response"].lower() or "unable" in out["validated_response"].lower()


def test_ac4_citation_whitelisted():
    """AC4: citation_url is always one of the allowed URLs (or default)."""
    for raw in [
        "Text. Last updated from sources: https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
        "Text. Last updated from sources: https://evil.com",
        "No citation.",
    ]:
        out = process_query(raw, source_url=ALLOWED_URLS[0])
        assert out["citation_url"] in ALLOWED_URLS or out["citation_url"] == DEFAULT_FUND_PAGE_URL


def test_ac5_five_sentence_cap():
    """AC5: Formatter enforces max 5 sentences."""
    long_text = ". ".join([f"Sentence {i}" for i in range(10)]) + "."
    out = process_query(long_text, source_url=ALLOWED_URLS[0])
    parts = [p.strip() for p in out["validated_response"].split(". ") if p.strip()]
    # Citation line may add one more "sentence" (Last updated...); count content sentences
    content = out["validated_response"].split(CITATION_PREFIX)[0]
    content_sentences = [s for s in content.replace("?", ".").replace("!", ".").split(".") if s.strip()]
    assert len(content_sentences) <= MAX_SENTENCES


def test_ac6_citation_appended_if_missing():
    """AC6: If response has no citation line, append with citation_url."""
    raw = "The fund has no exit load."
    out = process_query(raw, source_url=ALLOWED_URLS[0])
    assert CITATION_PREFIX in out["validated_response"]
    assert out["citation_url"] in out["validated_response"]
