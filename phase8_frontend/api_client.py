"""
Phase 8 — API client for Backend (Phase 7).

Uses the new API contract:
  POST /query  → {query, active_fund?, conversation_id?}  → {answer, citations, conversation_id}
  GET  /mutual-funds  → list of fund display names

No business logic lives here; this is a thin HTTP wrapper.
"""

import json
import urllib.request
import urllib.error

from .config import QUERY_ENDPOINT, MUTUAL_FUNDS_ENDPOINT, LAST_UPDATED_ENDPOINT


def send_query(
    query: str,
    *,
    active_fund: str | None = None,
    conversation_id: str | None = None,
) -> dict:
    """
    Send a user query to POST /query with the new contract.

    Returns dict with:
      answer:          str
      citations:       list[str]
      conversation_id: str
      error:           str | None
    """
    if not query or not query.strip():
        return {"answer": "Please enter a message.", "citations": [], "conversation_id": conversation_id or "", "error": None}

    payload: dict = {"query": query.strip()}
    if active_fund:
        payload["active_fund"] = active_fund
    if conversation_id:
        payload["conversation_id"] = conversation_id

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        QUERY_ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return {
                "answer": body.get("answer", ""),
                "citations": body.get("citations", []),
                "conversation_id": body.get("conversation_id", conversation_id or ""),
                "error": None,
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else str(e)
        return {"answer": "", "citations": [], "conversation_id": conversation_id or "", "error": f"Server error ({e.code}): {err_body}"}
    except urllib.error.URLError as e:
        return {"answer": "", "citations": [], "conversation_id": conversation_id or "", "error": f"Could not reach backend: {e.reason}"}
    except Exception as e:
        return {"answer": "", "citations": [], "conversation_id": conversation_id or "", "error": str(e)}


def fetch_mutual_funds() -> dict:
    """
    Fetch the list of supported fund names from GET /mutual-funds.

    Returns dict with:
      funds: list[str]
      error: str | None
    """
    req = urllib.request.Request(MUTUAL_FUNDS_ENDPOINT, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            funds = json.loads(resp.read().decode("utf-8"))
            return {"funds": funds if isinstance(funds, list) else [], "error": None}
    except urllib.error.HTTPError as e:
        return {"funds": [], "error": f"Server error ({e.code})"}
    except urllib.error.URLError as e:
        return {"funds": [], "error": f"Could not reach backend: {e.reason}"}
    except Exception as e:
        return {"funds": [], "error": str(e)}


def fetch_last_updated() -> dict:
    """
    Fetch the last data-refresh timestamp from GET /last-updated.

    Returns dict with:
      last_updated_utc: str | None
      status: str
      error: str | None
    """
    req = urllib.request.Request(LAST_UPDATED_ENDPOINT, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {**data, "error": None}
    except urllib.error.HTTPError as e:
        return {"last_updated_utc": None, "status": "error", "error": f"Server error ({e.code})"}
    except urllib.error.URLError as e:
        return {"last_updated_utc": None, "status": "error", "error": f"Could not reach backend: {e.reason}"}
    except Exception as e:
        return {"last_updated_utc": None, "status": "error", "error": str(e)}


# Legacy alias kept for backward compat with write_sample_outputs / old tests
def send_message(message: str) -> dict:
    """Legacy wrapper: maps old {message} → new {query} contract."""
    result = send_query(message)
    return {
        "response": result["answer"],
        "citation_url": result["citations"][0] if result["citations"] else None,
        "error": result.get("error"),
    }
