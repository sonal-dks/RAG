"""
Phase 5 unit and acceptance tests.

Uses mocked Groq client so no API key is required.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from phase5_response_generation import process_query
from phase5_response_generation.config import (
    GROQ_MODEL,
    MAX_TOKENS,
    SYSTEM_PROMPT,
    TEMPERATURE,
    TOP_P,
)
from phase5_response_generation.pipeline import INSUFFICIENT_CONTEXT_MARKER
from phase5_response_generation.prompt_builder import build_user_message, get_system_prompt


# --- Unit: prompt_builder ---


def test_build_user_message_includes_context_and_question():
    ctx = "Fund X has expense ratio 0.5%.\nSource: https://example.com"
    q = "What is the expense ratio?"
    msg = build_user_message(ctx, q)
    assert "CONTEXT:" in msg
    assert "USER QUESTION:" in msg
    assert "ANSWER:" in msg
    assert "Fund X" in msg
    assert q in msg


def test_build_user_message_empty_context():
    msg = build_user_message("", "What is NAV?")
    assert "CONTEXT:" in msg
    assert "(No context provided.)" in msg
    assert "USER QUESTION:" in msg
    assert "What is NAV?" in msg


def test_get_system_prompt_non_empty_and_contains_rules():
    prompt = get_system_prompt()
    assert len(prompt) > 0
    assert "Quant Mutual Fund" in prompt or "Groww" in prompt
    assert "CONTEXT" in prompt
    assert "5 sentences" in prompt or "5 sentences" in prompt.lower()
    assert "Last updated from sources" in prompt


# --- Unit: config ---


def test_generation_params_per_architecture():
    assert TEMPERATURE == 0.0
    assert MAX_TOKENS == 300
    assert TOP_P == 1.0
    assert "llama" in GROQ_MODEL.lower() or "mixtral" in GROQ_MODEL.lower()


# --- Unit + Integration: pipeline with mocked Groq ---


def test_process_query_insufficient_context_empty_string():
    out = process_query("What is the expense ratio?", "", sufficient=True)
    assert out["raw_response"] == INSUFFICIENT_CONTEXT_MARKER
    assert out["model_used"] is None
    assert out["api_called"] is False


def test_process_query_insufficient_context_message():
    out = process_query(
        "What is NAV?",
        INSUFFICIENT_CONTEXT_MARKER,
        sufficient=True,
    )
    assert out["raw_response"] == INSUFFICIENT_CONTEXT_MARKER
    assert out["api_called"] is False


def test_process_query_sufficient_false():
    out = process_query(
        "What is NAV?",
        "Some context here.",
        sufficient=False,
    )
    assert out["raw_response"] == INSUFFICIENT_CONTEXT_MARKER
    assert out["api_called"] is False


def test_process_query_empty_user_query():
    out = process_query("", "Context here", sufficient=True)
    assert out["raw_response"] == INSUFFICIENT_CONTEXT_MARKER
    assert out["api_called"] is False


def test_process_query_whitespace_only_user_query():
    out = process_query("   ", "Context here", sufficient=True)
    assert out["raw_response"] == INSUFFICIENT_CONTEXT_MARKER
    assert out["api_called"] is False


@patch("phase5_response_generation.generator._get_client")
def test_process_query_single_llm_call(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="The expense ratio is 0.5%. Last updated from sources: https://groww.in/mf/quant-small-cap."))]
    )
    mock_get_client.return_value = mock_client

    out = process_query(
        "What is the expense ratio?",
        "Expense ratio: 0.5%.\nSource: https://groww.in/mf/quant-small-cap",
        sufficient=True,
    )
    assert out["api_called"] is True
    assert out["model_used"] == GROQ_MODEL
    assert "expense ratio" in out["raw_response"].lower() or "0.5" in out["raw_response"]
    mock_client.chat.completions.create.assert_called_once()


@patch("phase5_response_generation.generator._get_client")
def test_process_query_prompt_assembly_passed_to_groq(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Answer."))]
    )
    mock_get_client.return_value = mock_client

    process_query(
        "What is the NAV?",
        "NAV is 100.\nSource: https://x.in",
        sufficient=True,
    )
    call = mock_client.chat.completions.create.call_args
    messages = call.kwargs["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "CONTEXT:" in messages[1]["content"]
    assert "USER QUESTION:" in messages[1]["content"]
    assert "What is the NAV?" in messages[1]["content"]
    assert "NAV is 100" in messages[1]["content"]
    assert call.kwargs["temperature"] == 0.0
    assert call.kwargs["max_tokens"] == 300
    assert call.kwargs["top_p"] == 1.0
    assert call.kwargs["model"] == GROQ_MODEL


@patch("phase5_response_generation.generator._get_client")
def test_process_query_missing_api_key_returns_service_unavailable(mock_get_client):
    mock_get_client.side_effect = ValueError("Missing GROQ_API_KEY")
    out = process_query("What is NAV?", "Some context", sufficient=True)
    assert out["api_called"] is False
    assert (
        "temporarily unavailable" in out["raw_response"].lower()
        or "try again" in out["raw_response"].lower()
        or "not configured" in out["raw_response"].lower()
        or "GROQ_API_KEY" in out["raw_response"]
    )
    assert out["model_used"] is None


def test_process_query_invalid_input_non_string_query():
    out = process_query(None, "Context", sufficient=True)
    assert out["raw_response"] == INSUFFICIENT_CONTEXT_MARKER
    assert out["api_called"] is False


# --- Acceptance criteria ---


def test_ac1_output_has_required_keys():
    """AC1: Output has raw_response, model_used, api_called."""
    out = process_query("Q?", "", sufficient=False)
    assert "raw_response" in out
    assert "model_used" in out
    assert "api_called" in out
    assert isinstance(out["raw_response"], str)
    assert isinstance(out["api_called"], bool)


def test_ac2_insufficient_context_no_api_call():
    """AC2: When context insufficient, no Groq call; raw_response is insufficient message."""
    out = process_query("What is NAV?", INSUFFICIENT_CONTEXT_MARKER, sufficient=True)
    assert out["api_called"] is False
    assert out["raw_response"] == INSUFFICIENT_CONTEXT_MARKER


def test_ac3_single_call_per_query():
    """AC3: Only one LLM call per user query when context is sufficient."""
    with patch("phase5_response_generation.generator._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Response."))]
        )
        mock_get_client.return_value = mock_client
        process_query("Query?", "Context.", sufficient=True)
        mock_client.chat.completions.create.assert_called_once()


def test_ac4_api_key_from_environment():
    """AC4: Generator reads API key from environment (no hardcode); raises if missing."""
    from phase5_response_generation.generator import _get_client
    with patch("phase5_response_generation.generator.load_dotenv"):
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False):
            with pytest.raises(ValueError) as exc_info:
                _get_client()
            assert "GROQ_API_KEY" in str(exc_info.value)


def test_ac5_generation_params_applied():
    """AC5: temperature=0, max_tokens=300, top_p=1.0 passed to API."""
    with patch("phase5_response_generation.generator._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Ok."))]
        )
        mock_get_client.return_value = mock_client
        process_query("Q", "C", sufficient=True)
        call = mock_client.chat.completions.create.call_args
        assert call.kwargs["temperature"] == 0.0
        assert call.kwargs["max_tokens"] == 300
        assert call.kwargs["top_p"] == 1.0


def test_ac6_sufficient_context_returns_llm_response():
    """AC6: When context sufficient, raw_response is from LLM (or fallback)."""
    with patch("phase5_response_generation.generator._get_client") as mock_get_client:
        mock_client = MagicMock()
        expected = "The NAV is 100. Last updated from sources: https://groww.in/x."
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=expected))]
        )
        mock_get_client.return_value = mock_client
        out = process_query("What is NAV?", "NAV 100. Source: https://groww.in/x", sufficient=True)
        assert out["raw_response"] == expected
        assert out["model_used"] == GROQ_MODEL
