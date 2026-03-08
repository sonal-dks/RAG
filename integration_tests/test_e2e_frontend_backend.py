"""
End-to-end integration tests: Phase 8 (Frontend) ↔ Phase 7 (Backend) contract.

Verifies that the Frontend api_client functions produce/consume the right shapes
for the Backend API.
"""

import json
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from phase7_backend.app import app


def _mock_urlopen(body_bytes: bytes):
    mock_resp = MagicMock()
    mock_resp.read.return_value = body_bytes
    mock_resp.__enter__ = lambda self: self
    mock_resp.__exit__ = lambda self, *a: None
    return mock_resp


# ── send_query contract ───────────────────────────────────────────────────


def test_e2e_frontend_send_query_shape():
    """send_query returns {answer, citations, conversation_id, error} matching backend."""
    from phase8_frontend.api_client import send_query

    resp_json = json.dumps({
        "answer": "The expense ratio is 0.77%.",
        "citations": ["https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"],
        "conversation_id": "c1",
    }).encode("utf-8")

    with patch("phase8_frontend.api_client.urllib.request.urlopen", return_value=_mock_urlopen(resp_json)):
        result = send_query("What is the expense ratio?", active_fund="Quant Small Cap Fund", conversation_id="c1")
    assert result["answer"] == "The expense ratio is 0.77%."
    assert result["citations"] == ["https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"]
    assert result["conversation_id"] == "c1"
    assert result["error"] is None


def test_e2e_frontend_send_query_payload_matches_backend():
    """send_query sends {query, active_fund, conversation_id} which POST /query expects."""
    from phase8_frontend.api_client import send_query

    with patch("phase8_frontend.api_client.urllib.request.urlopen", return_value=_mock_urlopen(
        b'{"answer":"ok","citations":[],"conversation_id":"c1"}'
    )) as mock_uo:
        send_query("What is the NAV?", active_fund="Quant Mid Cap Fund", conversation_id="c1")
    req = mock_uo.call_args[0][0]
    payload = json.loads(req.data.decode("utf-8"))
    assert payload == {"query": "What is the NAV?", "active_fund": "Quant Mid Cap Fund", "conversation_id": "c1"}


# ── fetch_mutual_funds contract ───────────────────────────────────────────


def test_e2e_frontend_fetch_mutual_funds_shape():
    """fetch_mutual_funds returns {funds, error} matching GET /mutual-funds."""
    from phase8_frontend.api_client import fetch_mutual_funds

    backend_resp = json.dumps([
        "Quant Small Cap Fund", "Quant Mid Cap Fund",
    ]).encode("utf-8")
    with patch("phase8_frontend.api_client.urllib.request.urlopen", return_value=_mock_urlopen(backend_resp)):
        result = fetch_mutual_funds()
    assert result["funds"] == ["Quant Small Cap Fund", "Quant Mid Cap Fund"]
    assert result["error"] is None


# ── fetch_last_updated contract ───────────────────────────────────────────


def test_e2e_frontend_fetch_last_updated_shape():
    """fetch_last_updated returns {last_updated_utc, status, error} matching GET /last-updated."""
    from phase8_frontend.api_client import fetch_last_updated

    backend_resp = json.dumps({
        "last_updated_utc": "2026-03-07T13:00:00+00:00",
        "chunks_indexed": 50,
        "status": "success",
    }).encode("utf-8")
    with patch("phase8_frontend.api_client.urllib.request.urlopen", return_value=_mock_urlopen(backend_resp)):
        result = fetch_last_updated()
    assert result["last_updated_utc"] == "2026-03-07T13:00:00+00:00"
    assert result["status"] == "success"
    assert result["error"] is None


# ── Legacy send_message still works with /chat ────────────────────────────


def test_e2e_frontend_legacy_send_message():
    """Legacy send_message returns {response, citation_url, error}."""
    from phase8_frontend.api_client import send_message

    resp_json = json.dumps({
        "answer": "Hello!",
        "citations": ["https://groww.in/x"],
        "conversation_id": "c1",
    }).encode("utf-8")
    with patch("phase8_frontend.api_client.urllib.request.urlopen", return_value=_mock_urlopen(resp_json)):
        result = send_message("Hi")
    assert "response" in result and "citation_url" in result and "error" in result
    assert result["error"] is None


# ── Real API via TestClient ───────────────────────────────────────────────


def test_e2e_api_response_consumable_by_frontend():
    """POST /query response can be directly consumed by send_query's parsing logic."""
    tc = TestClient(app)
    r = tc.post("/query", json={"query": "Hello"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data and isinstance(data["answer"], str)
    assert "citations" in data and isinstance(data["citations"], list)
    assert "conversation_id" in data and isinstance(data["conversation_id"], str)


def test_e2e_api_mutual_funds_consumable_by_frontend():
    """GET /mutual-funds response is a list of strings, consumable by fetch_mutual_funds."""
    tc = TestClient(app)
    r = tc.get("/mutual-funds")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and all(isinstance(f, str) for f in data)


def test_e2e_api_last_updated_consumable_by_frontend():
    """GET /last-updated response has last_updated_utc and status, consumable by fetch_last_updated."""
    tc = TestClient(app)
    r = tc.get("/last-updated")
    assert r.status_code == 200
    data = r.json()
    assert "last_updated_utc" in data and "status" in data
