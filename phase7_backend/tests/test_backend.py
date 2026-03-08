"""
Phase 7 unit and acceptance tests.

Covers:
  - Pipeline (run_rag): guardrail blocks, no-fund clarification, active_fund prepend, full flow
  - API endpoints: POST /query (new contract), GET /mutual-funds, POST /chat (legacy), GET /health
  - Acceptance criteria (AC1–AC7)
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from phase7_backend.app import app
from phase7_backend.config import FUND_DISPLAY_NAMES
from phase7_backend.pipeline import run_rag


# ---------------------------------------------------------------------------
# Pipeline — Phase 2 blocks (no Phase 4/5 needed)
# ---------------------------------------------------------------------------


class TestPipelineGuardrails:
    def test_pii_blocked(self):
        result = run_rag("My PAN is ABCDE1234F")
        assert "answer" in result and "citations" in result
        resp = result["answer"].lower()
        assert any(kw in resp for kw in ("personal", "sensitive", "pan", "cannot"))

    def test_advice_blocked(self):
        result = run_rag("Should I invest in Quant Small Cap?")
        assert "answer" in result
        resp = result["answer"].lower()
        assert any(kw in resp for kw in ("investment advice", "unable", "advice"))

    def test_empty_message(self):
        result = run_rag("")
        assert result["answer"]
        assert result["citations"] == []

    def test_none_message(self):
        result = run_rag(None)
        assert result["answer"]
        assert result["citation_url"] is None

    def test_no_fund_specified(self):
        result = run_rag("What is the expense ratio?")
        resp = result["answer"].lower()
        assert any(kw in resp for kw in ("specify", "which", "fund"))
        assert result["citations"] == []


# ---------------------------------------------------------------------------
# Pipeline — active_fund context
# ---------------------------------------------------------------------------


class TestActiveFundContext:
    @patch("phase7_backend.pipeline.retrieval_process")
    @patch("phase7_backend.pipeline.generation_process")
    def test_active_fund_resolves_ambiguous_query(self, mock_gen, mock_ret):
        """When active_fund is set, a bare query like 'What is the NAV?' should resolve."""
        mock_ret.return_value = {
            "retrieved_context": "NAV is 123.45. Source: https://groww.in/mutual-funds/quant-mid-cap-fund-direct-growth",
            "chunks": [{"source_url": "https://groww.in/mutual-funds/quant-mid-cap-fund-direct-growth"}],
            "sufficient": True,
        }
        mock_gen.return_value = {
            "raw_response": "The NAV is 123.45. Last updated from sources: https://groww.in/mutual-funds/quant-mid-cap-fund-direct-growth",
            "model_used": "llama-3.3-70b-versatile",
            "api_called": True,
        }
        result = run_rag("What is the NAV?", active_fund="Quant Mid Cap Fund")
        assert "answer" in result
        assert result["citations"]

    @patch("phase7_backend.pipeline.retrieval_process")
    @patch("phase7_backend.pipeline.generation_process")
    def test_active_fund_not_prepended_when_already_mentioned(self, mock_gen, mock_ret):
        """If the query already contains the fund name, don't duplicate it."""
        mock_ret.return_value = {
            "retrieved_context": "Expense ratio 0.77%.",
            "chunks": [{"source_url": "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"}],
            "sufficient": True,
        }
        mock_gen.return_value = {
            "raw_response": "The expense ratio of Quant Small Cap Fund is 0.77%.",
            "model_used": "llama-3.3-70b-versatile",
            "api_called": True,
        }
        result = run_rag(
            "What is the expense ratio of Quant Small Cap Fund?",
            active_fund="Quant Small Cap Fund",
        )
        assert "answer" in result

    def test_without_active_fund_asks_for_clarification(self):
        result = run_rag("What is the NAV?")
        assert any(kw in result["answer"].lower() for kw in ("specify", "which", "fund"))


# ---------------------------------------------------------------------------
# Pipeline — full flow (mock Phase 4 & 5)
# ---------------------------------------------------------------------------


class TestPipelineFullFlowMocked:
    @patch("phase7_backend.pipeline.retrieval_process")
    @patch("phase7_backend.pipeline.generation_process")
    def test_full_flow(self, mock_gen, mock_ret):
        mock_ret.return_value = {
            "retrieved_context": "Expense ratio 0.77%. Source: https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
            "chunks": [{"source_url": "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"}],
            "sufficient": True,
        }
        mock_gen.return_value = {
            "raw_response": "The expense ratio is 0.77%. Last updated from sources: https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
            "model_used": "llama-3.3-70b-versatile",
            "api_called": True,
        }
        result = run_rag("What is the expense ratio of Quant Small Cap Fund?")
        assert "answer" in result and "citations" in result
        assert "0.77" in result["answer"] or "expense" in result["answer"].lower()
        assert result["citations"] and "groww.in" in result["citations"][0]


# ---------------------------------------------------------------------------
# API — POST /query (new contract)
# ---------------------------------------------------------------------------


class TestPostQuery:
    client = TestClient(app)

    @patch("phase7_backend.app.run_rag")
    def test_returns_200_with_new_schema(self, mock_run):
        mock_run.return_value = {
            "answer": "The expense ratio is 0.77%.",
            "citations": ["https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"],
            "citation_url": "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
        }
        r = self.client.post("/query", json={"query": "What is the expense ratio of Quant Small Cap Fund?"})
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "citations" in data and isinstance(data["citations"], list)
        assert "conversation_id" in data and isinstance(data["conversation_id"], str)

    @patch("phase7_backend.app.run_rag")
    def test_passes_active_fund(self, mock_run):
        mock_run.return_value = {"answer": "NAV is 123.", "citations": [], "citation_url": None}
        self.client.post("/query", json={
            "query": "What is the NAV?",
            "active_fund": "Quant Mid Cap Fund",
        })
        mock_run.assert_called_once_with("What is the NAV?", active_fund="Quant Mid Cap Fund")

    @patch("phase7_backend.app.run_rag")
    def test_returns_provided_conversation_id(self, mock_run):
        mock_run.return_value = {"answer": "hi", "citations": [], "citation_url": None}
        r = self.client.post("/query", json={
            "query": "hi",
            "conversation_id": "conv-abc-123",
        })
        assert r.json()["conversation_id"] == "conv-abc-123"

    @patch("phase7_backend.app.run_rag")
    def test_generates_conversation_id_if_missing(self, mock_run):
        mock_run.return_value = {"answer": "hi", "citations": [], "citation_url": None}
        r = self.client.post("/query", json={"query": "hi"})
        cid = r.json()["conversation_id"]
        assert cid and len(cid) > 8

    def test_empty_query_rejected(self):
        r = self.client.post("/query", json={"query": ""})
        assert r.status_code == 422

    def test_missing_query_rejected(self):
        r = self.client.post("/query", json={})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# API — GET /mutual-funds
# ---------------------------------------------------------------------------


class TestGetMutualFunds:
    client = TestClient(app)

    def test_returns_list_of_fund_names(self):
        r = self.client.get("/mutual-funds")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 10
        assert "Quant Small Cap Fund" in data

    def test_matches_config(self):
        r = self.client.get("/mutual-funds")
        assert r.json() == FUND_DISPLAY_NAMES


# ---------------------------------------------------------------------------
# API — GET /last-updated
# ---------------------------------------------------------------------------


class TestGetLastUpdated:
    client = TestClient(app)

    def test_returns_200(self):
        r = self.client.get("/last-updated")
        assert r.status_code == 200
        data = r.json()
        assert "last_updated_utc" in data
        assert "status" in data

    def test_never_run_when_no_file(self, tmp_path):
        with patch("phase7_backend.app.LAST_UPDATED_PATH", tmp_path / "nonexistent.json"):
            r = self.client.get("/last-updated")
            assert r.status_code == 200
            assert r.json()["status"] == "never_run"

    def test_returns_data_when_file_exists(self, tmp_path):
        import json
        lu = tmp_path / "last_updated.json"
        lu.write_text(json.dumps({"last_updated_utc": "2026-03-07T13:00:00+00:00", "chunks_indexed": 50, "status": "success"}))
        with patch("phase7_backend.app.LAST_UPDATED_PATH", lu):
            r = self.client.get("/last-updated")
            assert r.status_code == 200
            data = r.json()
            assert data["status"] == "success"
            assert data["last_updated_utc"] == "2026-03-07T13:00:00+00:00"
            assert data["chunks_indexed"] == 50


# ---------------------------------------------------------------------------
# API — POST /chat (legacy) & GET /health
# ---------------------------------------------------------------------------


class TestLegacyAndHealth:
    client = TestClient(app)

    def test_health(self):
        r = self.client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_post_chat_legacy(self):
        r = self.client.post("/chat", json={"message": "Hi"})
        assert r.status_code == 200
        data = r.json()
        assert "response" in data
        assert "citation_url" in data


# ---------------------------------------------------------------------------
# Acceptance Criteria
# ---------------------------------------------------------------------------


class TestAcceptanceCriteria:
    client = TestClient(app)

    def test_ac1_query_response_shape(self):
        """AC1: POST /query returns {answer, citations, conversation_id}."""
        r = self.client.post("/query", json={"query": "Hello"})
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"answer", "citations", "conversation_id"}

    def test_ac2_guardrail_block_returns_canned(self):
        """AC2: PII input is blocked with a canned message."""
        result = run_rag("My Aadhaar is 1234 5678 9012")
        assert result["answer"]
        assert any(kw in result["answer"].lower() for kw in ("personal", "sensitive", "cannot"))

    def test_ac3_no_fund_returns_clarification(self):
        """AC3: No fund → clarification message, empty citations."""
        result = run_rag("What is the NAV?")
        assert "fund" in result["answer"].lower()
        assert result["citations"] == []

    @patch("phase7_backend.pipeline.retrieval_process")
    @patch("phase7_backend.pipeline.generation_process")
    def test_ac4_active_fund_resolves_context(self, mock_gen, mock_ret):
        """AC4: active_fund allows bare queries to resolve to a fund."""
        mock_ret.return_value = {
            "retrieved_context": "NAV 200.",
            "chunks": [{"source_url": "https://groww.in/mutual-funds/quant-focused-fund-direct-growth"}],
            "sufficient": True,
        }
        mock_gen.return_value = {
            "raw_response": "The NAV is 200.",
            "model_used": "mock",
            "api_called": True,
        }
        result = run_rag("What is the NAV?", active_fund="Quant Focused Fund")
        assert result["answer"]
        assert result["citations"]

    def test_ac5_stateless_no_session(self):
        """AC5: Each run_rag call is independent (stateless)."""
        r1 = run_rag("Hi")
        r2 = run_rag("Compare Quant Small Cap and Mid Cap")
        assert "answer" in r1 and "answer" in r2
        assert r1["answer"] and r2["answer"]

    def test_ac6_mutual_funds_endpoint(self):
        """AC6: GET /mutual-funds returns the 10 fund display names."""
        r = self.client.get("/mutual-funds")
        assert r.status_code == 200
        assert len(r.json()) == 10

    def test_ac7_cors_headers(self):
        """AC7: CORS headers are present (Access-Control-Allow-Origin)."""
        r = self.client.options(
            "/query",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
        )
        assert "access-control-allow-origin" in r.headers
