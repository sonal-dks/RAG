"""
Phase 8 — unit and acceptance tests.

Covers (matching architecture.md §8.10 and §8.11):
  - API client: send_query (new contract), fetch_mutual_funds, fetch_last_updated, legacy send_message
  - Config: endpoints, sample questions
  - Chat flow: user sends query → backend returns response
  - Fund memory: active_fund passed with query (via dropdown)
  - Context clearing: no active_fund → explicit fund required
  - Conversation switching: separate conversations retain own state
  - Error states: API failure → error returned
  - Acceptance criteria (AC1–AC7)
"""

from unittest.mock import patch, MagicMock

import pytest

from phase8_frontend.api_client import send_query, fetch_mutual_funds, fetch_last_updated, send_message
from phase8_frontend.config import (
    BACKEND_URL,
    QUERY_ENDPOINT,
    MUTUAL_FUNDS_ENDPOINT,
    LAST_UPDATED_ENDPOINT,
    QUICK_PROMPTS,
    SAMPLE_QUESTIONS_POOL,
    NUM_SAMPLE_QUESTIONS,
    get_sample_questions,
)


# ── Helper: mock a successful urlopen response ───────────────────────────

def _mock_urlopen_response(body_bytes: bytes):
    mock_resp = MagicMock()
    mock_resp.read.return_value = body_bytes
    mock_resp.__enter__ = lambda self: self
    mock_resp.__exit__ = lambda self, *a: None
    return mock_resp


# ══════════════════════════════════════════════════════════════════════════
# send_query — API contract
# ══════════════════════════════════════════════════════════════════════════


class TestSendQuery:

    def test_empty_returns_placeholder(self):
        r = send_query("")
        assert r["answer"] == "Please enter a message."
        assert r["citations"] == []
        assert r["error"] is None

    def test_whitespace_only(self):
        r = send_query("   ")
        assert "Please" in r["answer"]

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"answer":"NAV is 200.","citations":["https://groww.in/x"],"conversation_id":"c1"}'
        )
        r = send_query("What is the NAV?")
        assert r["answer"] == "NAV is 200."
        assert r["citations"] == ["https://groww.in/x"]
        assert r["conversation_id"] == "c1"
        assert r["error"] is None

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_sends_active_fund(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"answer":"ok","citations":[],"conversation_id":"c1"}'
        )
        send_query("What is the NAV?", active_fund="Quant Mid Cap Fund", conversation_id="c1")
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        import json
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["query"] == "What is the NAV?"
        assert payload["active_fund"] == "Quant Mid Cap Fund"
        assert payload["conversation_id"] == "c1"

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_omits_optional_fields_when_none(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"answer":"ok","citations":[],"conversation_id":"new"}'
        )
        send_query("Hi")
        req = mock_urlopen.call_args[0][0]
        import json
        payload = json.loads(req.data.decode("utf-8"))
        assert "active_fund" not in payload
        assert "conversation_id" not in payload

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen):
        import urllib.error
        err = urllib.error.HTTPError("http://x/query", 500, "fail", {}, None)
        err.fp = None
        mock_urlopen.side_effect = err
        r = send_query("Hi")
        assert r["error"] is not None and "500" in r["error"]
        assert r["answer"] == ""

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_connection_refused(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        r = send_query("Hi")
        assert r["error"] is not None
        assert "backend" in r["error"].lower() or "refused" in r["error"].lower()


# ══════════════════════════════════════════════════════════════════════════
# fetch_mutual_funds
# ══════════════════════════════════════════════════════════════════════════


class TestFetchMutualFunds:

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_response(
            b'["Quant Small Cap Fund","Quant Mid Cap Fund"]'
        )
        r = fetch_mutual_funds()
        assert r["funds"] == ["Quant Small Cap Fund", "Quant Mid Cap Fund"]
        assert r["error"] is None

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        r = fetch_mutual_funds()
        assert r["funds"] == []
        assert r["error"] is not None


# ══════════════════════════════════════════════════════════════════════════
# fetch_last_updated
# ══════════════════════════════════════════════════════════════════════════


class TestFetchLastUpdated:

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"last_updated_utc":"2026-03-07T13:00:00+00:00","chunks_indexed":50,"status":"success"}'
        )
        r = fetch_last_updated()
        assert r["last_updated_utc"] == "2026-03-07T13:00:00+00:00"
        assert r["status"] == "success"
        assert r["error"] is None

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_never_run(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"last_updated_utc":null,"status":"never_run"}'
        )
        r = fetch_last_updated()
        assert r["last_updated_utc"] is None
        assert r["status"] == "never_run"

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("fail")
        r = fetch_last_updated()
        assert r["error"] is not None
        assert r["last_updated_utc"] is None


# ══════════════════════════════════════════════════════════════════════════
# Legacy send_message
# ══════════════════════════════════════════════════════════════════════════


class TestLegacySendMessage:

    def test_empty(self):
        r = send_message("")
        assert "response" in r and "citation_url" in r and "error" in r

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_maps_to_new_contract(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"answer":"The NAV is 100.","citations":["https://groww.in/x"],"conversation_id":"c1"}'
        )
        r = send_message("What is the NAV?")
        assert r["response"] == "The NAV is 100."
        assert r["citation_url"] == "https://groww.in/x"
        assert r["error"] is None


# ══════════════════════════════════════════════════════════════════════════
# Config
# ══════════════════════════════════════════════════════════════════════════


class TestConfig:

    def test_backend_url(self):
        assert BACKEND_URL and "http" in BACKEND_URL

    def test_query_endpoint(self):
        assert QUERY_ENDPOINT.endswith("/query")

    def test_mutual_funds_endpoint(self):
        assert MUTUAL_FUNDS_ENDPOINT.endswith("/mutual-funds")

    def test_last_updated_endpoint(self):
        assert LAST_UPDATED_ENDPOINT.endswith("/last-updated")

    def test_quick_prompts_non_empty(self):
        assert len(QUICK_PROMPTS) >= 1
        assert all(isinstance(p, str) and p for p in QUICK_PROMPTS)

    def test_sample_questions_pool_size(self):
        assert len(SAMPLE_QUESTIONS_POOL) >= NUM_SAMPLE_QUESTIONS

    def test_get_sample_questions_returns_correct_count(self):
        qs = get_sample_questions()
        assert len(qs) == NUM_SAMPLE_QUESTIONS
        assert all(isinstance(q, str) for q in qs)

    def test_get_sample_questions_varies(self):
        s1 = get_sample_questions(seed=1)
        s2 = get_sample_questions(seed=2)
        assert s1 != s2

    def test_get_sample_questions_deterministic_with_seed(self):
        assert get_sample_questions(seed=42) == get_sample_questions(seed=42)


# ══════════════════════════════════════════════════════════════════════════
# Chat flow (§8.10)
# ══════════════════════════════════════════════════════════════════════════


class TestChatFlow:

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_user_query_returns_answer_and_citations(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"answer":"Expense ratio is 0.77%.","citations":["https://groww.in/x"],"conversation_id":"c1"}'
        )
        r = send_query("What is the expense ratio?")
        assert r["answer"] and r["citations"]
        assert r["error"] is None


# ══════════════════════════════════════════════════════════════════════════
# Fund memory via dropdown (§8.10)
# ══════════════════════════════════════════════════════════════════════════


class TestFundMemory:

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_active_fund_sent_in_payload(self, mock_urlopen):
        """Fund selected from dropdown → active_fund included in request."""
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"answer":"ok","citations":[],"conversation_id":"c1"}'
        )
        send_query("What is the NAV?", active_fund="Quant Small Cap Fund")
        import json
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["active_fund"] == "Quant Small Cap Fund"

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_no_active_fund_when_cleared(self, mock_urlopen):
        """Dropdown cleared → active_fund omitted from payload."""
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"answer":"ok","citations":[],"conversation_id":"c1"}'
        )
        send_query("What is the NAV?", active_fund=None)
        import json
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert "active_fund" not in payload


# ══════════════════════════════════════════════════════════════════════════
# Conversation switching (§8.10)
# ══════════════════════════════════════════════════════════════════════════


class TestConversationSwitching:

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_different_conversations_get_own_conversation_id(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"answer":"ok","citations":[],"conversation_id":"c1"}'
        )
        send_query("Q1", conversation_id="conv-A")
        send_query("Q2", conversation_id="conv-B")
        calls = mock_urlopen.call_args_list
        import json
        p1 = json.loads(calls[0][0][0].data.decode("utf-8"))
        p2 = json.loads(calls[1][0][0].data.decode("utf-8"))
        assert p1["conversation_id"] == "conv-A"
        assert p2["conversation_id"] == "conv-B"


# ══════════════════════════════════════════════════════════════════════════
# Error states (§8.10)
# ══════════════════════════════════════════════════════════════════════════


class TestErrorStates:

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_api_failure_returns_friendly_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        r = send_query("Q?")
        assert r["error"]
        assert r["answer"] == ""


# ══════════════════════════════════════════════════════════════════════════
# Acceptance Criteria (§8.11)
# ══════════════════════════════════════════════════════════════════════════


class TestAcceptanceCriteria:

    def test_ac1_ui_modules_exist(self):
        """AC1: UI modules exist (app, api_client, config)."""
        from phase8_frontend import app
        from phase8_frontend import api_client
        from phase8_frontend import config
        assert hasattr(api_client, "send_query")
        assert hasattr(api_client, "fetch_mutual_funds")
        assert hasattr(config, "QUERY_ENDPOINT")
        assert hasattr(config, "MUTUAL_FUNDS_ENDPOINT")

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_ac2_fund_context_memory_in_payload(self, mock_urlopen):
        """AC2: active_fund (from dropdown) sent with every query."""
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"answer":"ok","citations":[],"conversation_id":"c1"}'
        )
        send_query("What is the P/E?", active_fund="Quant Focused Fund", conversation_id="c1")
        import json
        payload = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
        assert payload["active_fund"] == "Quant Focused Fund"
        assert payload["conversation_id"] == "c1"

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_ac3_conversation_id_passed(self, mock_urlopen):
        """AC3: conversation_id sent with every query."""
        mock_urlopen.return_value = _mock_urlopen_response(
            b'{"answer":"ok","citations":[],"conversation_id":"abc-123"}'
        )
        r = send_query("Hi", conversation_id="abc-123")
        assert r["conversation_id"] == "abc-123"

    def test_ac4_api_client_no_business_logic(self):
        """AC4: Frontend does not run guardrails/LLM."""
        import inspect
        src = inspect.getsource(send_query)
        assert "guardrail" not in src.lower()
        assert "groq" not in src.lower()
        assert "chromadb" not in src.lower()

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_ac5_error_handling(self, mock_urlopen):
        """AC5: Network error → user-friendly error, not crash."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        r = send_query("Q?")
        assert r["error"]
        assert isinstance(r["error"], str)

    @patch("phase8_frontend.api_client.urllib.request.urlopen")
    def test_ac6_fetch_mutual_funds_for_dropdown(self, mock_urlopen):
        """AC6: GET /mutual-funds returns fund list (used to populate dropdown)."""
        mock_urlopen.return_value = _mock_urlopen_response(
            b'["Quant Small Cap Fund","Quant Mid Cap Fund","Quant Flexi Cap Fund"]'
        )
        r = fetch_mutual_funds()
        assert len(r["funds"]) == 3
        assert r["error"] is None

    def test_ac7_sample_questions_randomized(self):
        """AC7: Sample questions vary across new-chat sessions."""
        s1 = get_sample_questions(seed=10)
        s2 = get_sample_questions(seed=20)
        assert s1 != s2
