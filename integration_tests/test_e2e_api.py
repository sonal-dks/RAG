"""
End-to-end integration tests: Phase 7 API endpoints.

Uses FastAPI TestClient; exercises the API with the new contract:
  POST /query   → {query, active_fund?, conversation_id?} → {answer, citations, conversation_id}
  GET  /mutual-funds → list of fund names
  GET  /last-updated → {last_updated_utc, status, ...}
  POST /chat    → legacy {message} → {response, citation_url}
  GET  /health  → {status: "ok"}
"""

import pytest
from fastapi.testclient import TestClient

from phase7_backend.app import app

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────


def test_e2e_api_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ── POST /query — guardrails ─────────────────────────────────────────────


def test_e2e_api_query_pii_blocked():
    r = client.post("/query", json={"query": "My Aadhaar is 1234 5678 9012"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data and "citations" in data and "conversation_id" in data
    assert any(kw in data["answer"].lower() for kw in ("personal", "sensitive", "aadhaar", "cannot"))


def test_e2e_api_query_advice_blocked():
    r = client.post("/query", json={"query": "Should I invest in Quant ELSS?"})
    assert r.status_code == 200
    data = r.json()
    assert any(kw in data["answer"].lower() for kw in ("unable", "advice"))


def test_e2e_api_query_no_fund():
    r = client.post("/query", json={"query": "What is the expense ratio?"})
    assert r.status_code == 200
    data = r.json()
    assert any(kw in data["answer"].lower() for kw in ("specify", "which", "fund"))


def test_e2e_api_query_factual():
    r = client.post("/query", json={"query": "What is the expense ratio of Quant Small Cap Fund?"})
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] and isinstance(data["answer"], str)
    assert "conversation_id" in data


# ── POST /query — active_fund context ─────────────────────────────────────


def test_e2e_api_query_with_active_fund():
    """active_fund resolves a bare query so Phase 3 finds the fund."""
    r = client.post("/query", json={
        "query": "What is the NAV?",
        "active_fund": "Quant Mid Cap Fund",
    })
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    # Should NOT ask for clarification since active_fund is set
    assert "specify" not in data["answer"].lower() or "mid cap" in data["answer"].lower()


def test_e2e_api_query_returns_conversation_id():
    r = client.post("/query", json={"query": "Hi", "conversation_id": "conv-123"})
    assert r.status_code == 200
    assert r.json()["conversation_id"] == "conv-123"


def test_e2e_api_query_generates_conversation_id():
    r = client.post("/query", json={"query": "Hi"})
    assert r.status_code == 200
    cid = r.json()["conversation_id"]
    assert cid and len(cid) > 0


# ── POST /query — validation ─────────────────────────────────────────────


def test_e2e_api_query_empty_rejected():
    r = client.post("/query", json={"query": ""})
    assert r.status_code == 422


def test_e2e_api_query_missing_rejected():
    r = client.post("/query", json={})
    assert r.status_code == 422


# ── GET /mutual-funds ─────────────────────────────────────────────────────


def test_e2e_api_mutual_funds():
    r = client.get("/mutual-funds")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 10
    assert "Quant Small Cap Fund" in data
    assert "Quant ELSS Tax Saver Fund" in data


# ── GET /last-updated ─────────────────────────────────────────────────────


def test_e2e_api_last_updated():
    r = client.get("/last-updated")
    assert r.status_code == 200
    data = r.json()
    assert "last_updated_utc" in data
    assert "status" in data


# ── POST /chat (legacy) ──────────────────────────────────────────────────


def test_e2e_api_chat_legacy():
    r = client.post("/chat", json={"message": "Hi"})
    assert r.status_code == 200
    data = r.json()
    assert "response" in data and "citation_url" in data


# ── API response contract for Phase 8 ────────────────────────────────────


def test_e2e_api_response_contract():
    """Response shape matches Phase 8 send_query expectations: {answer, citations, conversation_id}."""
    r = client.post("/query", json={"query": "What is Quant Small Cap?"})
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {"answer", "citations", "conversation_id"}
    assert isinstance(data["answer"], str)
    assert isinstance(data["citations"], list)
    assert isinstance(data["conversation_id"], str)
