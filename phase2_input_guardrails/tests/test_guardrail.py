"""
Phase 2 — Unit tests with expected output and acceptance criteria.

Acceptance criteria (from architecture.md):
  AC1: PII in query → block with reason 'pii', canned_response = CANNED_PII.
  AC2: investment_advice intent → block, canned_response contains redirect URL.
  AC3: comparison_request intent → block, canned_response contains redirect URL.
  AC4: greeting/chitchat → block, canned_response is greeting + scope reminder.
  AC5: off_topic → block, canned_response = "I can only answer factual questions about the listed Quant Mutual Funds."
  AC6: factual_query → pass_through=True, intent='factual_query', query preserved.
  AC7: Empty/invalid input → block (off_topic).
  AC8: Output has required keys: pass_through; if block then reason + canned_response; if pass then intent + query.
"""

import pytest

from phase2_input_guardrails.config import (
    CANNED_GREETING,
    CANNED_OFF_TOPIC,
    CANNED_PII,
    DEFAULT_FUND_PAGE_URL,
)
from phase2_input_guardrails.guardrail import process_query


# --- Expected outputs (exact or substring) for comparison ---

EXPECTED_PII_RESPONSE = CANNED_PII

EXPECTED_OFF_TOPIC_RESPONSE = "I can only answer factual questions about the listed Quant Mutual Funds."

EXPECTED_GREETING_STARTS = "Hello! I can answer factual questions"

EXPECTED_ADVICE_REDIRECT_CONTAINS = "You can review the fund details here:"
EXPECTED_ADVICE_REDIRECT_URL = DEFAULT_FUND_PAGE_URL


def _is_block(result: dict) -> bool:
    return result.get("pass_through") is False


def _is_pass(result: dict) -> bool:
    return result.get("pass_through") is True


class TestOutputStructure:
    """AC8: Output has required keys."""

    def test_result_has_pass_through(self):
        result = process_query("What is the NAV of Quant Small Cap?")
        assert "pass_through" in result
        assert isinstance(result["pass_through"], bool)

    def test_block_has_reason_and_canned_response(self):
        result = process_query("Hi")
        assert _is_block(result)
        assert "reason" in result
        assert "canned_response" in result
        assert isinstance(result["canned_response"], str)
        assert len(result["canned_response"]) > 0

    def test_pass_has_intent_and_query(self):
        result = process_query("What is the expense ratio of Quant Small Cap Fund?")
        assert _is_pass(result)
        assert result.get("intent") == "factual_query"
        assert "query" in result
        assert result["query"] == "What is the expense ratio of Quant Small Cap Fund?"


class TestPIIBlock:
    """AC1: PII in query → block, reason=pii, canned_response = CANNED_PII."""

    @pytest.mark.parametrize(
        "user_input,expected_response",
        [
            ("My PAN is ABCDE1234F", EXPECTED_PII_RESPONSE),
            ("PAN: XYZAB9876K", EXPECTED_PII_RESPONSE),
            ("Aadhaar 1234 5678 9012", EXPECTED_PII_RESPONSE),
            ("Contact me at user@example.com", EXPECTED_PII_RESPONSE),
            ("Call 9876543210", EXPECTED_PII_RESPONSE),
            ("My number is +91 9876543210", EXPECTED_PII_RESPONSE),
        ],
    )
    def test_pii_detected_blocks_with_expected_message(self, user_input, expected_response):
        result = process_query(user_input)
        assert _is_block(result), f"Expected block for input: {user_input!r}"
        assert result["reason"] == "pii"
        assert result["canned_response"] == expected_response

    def test_pii_output_matches_expected_exactly(self):
        result = process_query("Please use PAN ABCDE1234F")
        assert result["canned_response"] == EXPECTED_PII_RESPONSE


class TestInvestmentAdviceBlock:
    """AC2: investment_advice → block, canned_response contains redirect URL."""

    @pytest.mark.parametrize(
        "user_input",
        [
            "Should I invest in Quant Small Cap?",
            "Can you recommend a fund?",
            "Which is the best fund?",
            "Will it go up?",
        ],
    )
    def test_advice_blocked_and_contains_redirect(self, user_input):
        result = process_query(user_input)
        assert _is_block(result)
        assert result["reason"] in ("investment_advice", "comparison_request")
        assert EXPECTED_ADVICE_REDIRECT_CONTAINS in result["canned_response"]
        assert EXPECTED_ADVICE_REDIRECT_URL in result["canned_response"]


class TestComparisonBlock:
    """AC3: comparison_request → block, canned_response contains redirect URL."""

    def test_comparison_blocked(self):
        result = process_query("Compare returns of Quant Small Cap and Quant Mid Cap")
        assert _is_block(result)
        assert EXPECTED_ADVICE_REDIRECT_CONTAINS in result["canned_response"]
        assert EXPECTED_ADVICE_REDIRECT_URL in result["canned_response"]


class TestGreetingBlock:
    """AC4: greeting/chitchat → block, greeting + scope reminder."""

    @pytest.mark.parametrize(
        "user_input",
        ["Hi", "Hello", "Good morning", "Thanks", "Bye"],
    )
    def test_greeting_blocked_with_expected_message(self, user_input):
        result = process_query(user_input)
        assert _is_block(result)
        assert result["reason"] == "greeting_chitchat"
        assert result["canned_response"].startswith(EXPECTED_GREETING_STARTS)
        assert "Quant" in result["canned_response"] or "factual" in result["canned_response"]

    def test_greeting_response_equals_config(self):
        result = process_query("Hello!")
        assert result["canned_response"] == CANNED_GREETING


class TestOffTopicBlock:
    """AC5: off_topic → block with exact off-topic message."""

    def test_off_topic_blocked(self):
        result = process_query("What is the weather today?")
        assert _is_block(result)
        assert result["reason"] == "off_topic"
        assert result["canned_response"] == EXPECTED_OFF_TOPIC_RESPONSE

    def test_off_topic_response_equals_config(self):
        result = process_query("Tell me about cricket")
        assert result["canned_response"] == CANNED_OFF_TOPIC


class TestFactualQueryPass:
    """AC6: factual_query → pass_through=True, intent=factual_query, query preserved."""

    @pytest.mark.parametrize(
        "user_input",
        [
            "What is the NAV of Quant Small Cap Fund?",
            "What is the expense ratio of Quant Small Cap Fund?",
            "List top 5 holdings of Quant ELSS",
            "Who manages Quant Infrastructure Fund?",
            "What is the exit load for Quant Flexi Cap?",
        ],
    )
    def test_factual_queries_pass(self, user_input):
        result = process_query(user_input)
        assert _is_pass(result), f"Expected pass for: {user_input!r}"
        assert result["intent"] == "factual_query"
        assert result["query"] == user_input

    def test_pass_output_no_canned_response(self):
        result = process_query("What is the AUM of Quant Large Cap?")
        assert result.get("canned_response") is None


class TestEmptyInvalidInput:
    """AC7: Empty or invalid input → block."""

    def test_empty_string_blocked(self):
        result = process_query("")
        assert _is_block(result)
        assert result["reason"] == "off_topic"

    def test_whitespace_only_blocked(self):
        result = process_query("   \n\t  ")
        assert _is_block(result)

    def test_none_equivalent_blocked(self):
        result = process_query("")
        assert _is_block(result)


class TestExpectedOutputComparison:
    """Compare actual output with expected output explicitly."""

    def test_pii_expected_vs_actual(self):
        actual = process_query("My PAN is ABCDE1234F")
        expected_message = CANNED_PII
        assert actual["canned_response"] == expected_message

    def test_off_topic_expected_vs_actual(self):
        actual = process_query("What is bitcoin?")
        assert actual["canned_response"] == CANNED_OFF_TOPIC

    def test_factual_expected_structure(self):
        actual = process_query("What is the NAV of Quant Small Cap?")
        expected = {
            "pass_through": True,
            "intent": "factual_query",
            "query": "What is the NAV of Quant Small Cap?",
            "canned_response": None,
        }
        assert actual["pass_through"] == expected["pass_through"]
        assert actual["intent"] == expected["intent"]
        assert actual["query"] == expected["query"]
        assert actual["canned_response"] is None


class TestAcceptanceCriteriaMet:
    """
    Acceptance criteria (from architecture.md) — all must pass before job is complete.
    """

    def test_ac1_pii_blocks_with_canned_message(self):
        """AC1: PII → block, reason=pii, canned_response = CANNED_PII."""
        r = process_query("PAN is ABCDE1234F")
        assert r["pass_through"] is False and r["reason"] == "pii" and r["canned_response"] == CANNED_PII

    def test_ac2_investment_advice_blocks_with_redirect(self):
        """AC2: investment_advice → block, response contains redirect URL."""
        r = process_query("Should I invest in Quant Small Cap?")
        assert r["pass_through"] is False
        assert EXPECTED_ADVICE_REDIRECT_URL in r["canned_response"]

    def test_ac3_comparison_blocks_with_redirect(self):
        """AC3: comparison_request → block, response contains redirect URL."""
        r = process_query("Compare Quant Small Cap and Quant Mid Cap")
        assert r["pass_through"] is False
        assert EXPECTED_ADVICE_REDIRECT_URL in r["canned_response"]

    def test_ac4_greeting_returns_scope_reminder(self):
        """AC4: greeting → block, greeting + scope reminder."""
        r = process_query("Hi")
        assert r["pass_through"] is False and r["reason"] == "greeting_chitchat"
        assert r["canned_response"] == CANNED_GREETING

    def test_ac5_off_topic_returns_exact_message(self):
        """AC5: off_topic → block, exact off-topic message."""
        r = process_query("What is the weather?")
        assert r["pass_through"] is False and r["reason"] == "off_topic"
        assert r["canned_response"] == CANNED_OFF_TOPIC

    def test_ac6_factual_passes_with_intent_and_query(self):
        """AC6: factual_query → pass_through=True, intent=factual_query, query preserved."""
        q = "What is the NAV of Quant Small Cap Fund?"
        r = process_query(q)
        assert r["pass_through"] is True and r["intent"] == "factual_query" and r["query"] == q

    def test_ac7_empty_input_blocked(self):
        """AC7: Empty/invalid input → block."""
        assert process_query("")["pass_through"] is False
        assert process_query("   ")["pass_through"] is False

    def test_ac8_output_structure_block(self):
        """AC8: Block output has pass_through, reason, canned_response."""
        r = process_query("Hi")
        assert "pass_through" in r and "reason" in r and "canned_response" in r
        assert r["pass_through"] is False

    def test_ac8_output_structure_pass(self):
        """AC8: Pass output has pass_through, intent, query."""
        r = process_query("What is the expense ratio of Quant ELSS?")
        assert "pass_through" in r and "intent" in r and "query" in r
        assert r["pass_through"] is True
