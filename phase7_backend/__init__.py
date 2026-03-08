"""
Phase 7 — Backend (FastAPI).

Hosts Phases 2–6; exposes POST /query, GET /mutual-funds, POST /chat.
"""

from .app import app
from .pipeline import run_rag

__all__ = ["app", "run_rag"]
