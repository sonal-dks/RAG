"""
Phase 8 — Frontend (three-panel chat UI).

Calls Backend (Phase 7) only; no business logic.
"""

from .api_client import send_query, fetch_mutual_funds, fetch_last_updated, send_message
from .config import BACKEND_URL, QUICK_PROMPTS, MUTUAL_FUNDS_ENDPOINT, LAST_UPDATED_ENDPOINT

__all__ = ["send_query", "fetch_mutual_funds", "fetch_last_updated", "send_message", "BACKEND_URL", "QUICK_PROMPTS", "MUTUAL_FUNDS_ENDPOINT", "LAST_UPDATED_ENDPOINT"]
