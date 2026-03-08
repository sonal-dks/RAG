"""
Phase 7 — FastAPI application.

Exposes:
  POST /query           — {query, active_fund?, conversation_id?} → {answer, citations, conversation_id}
  GET  /mutual-funds    — list of supported fund display names
  GET  /last-updated    — last data-refresh timestamp (written by scheduler)
  GET  /health          — liveness probe

Stateless; no PII storage.
"""

import json
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import FUND_DISPLAY_NAMES, LAST_UPDATED_PATH
from .pipeline import run_rag

# Ensure backend cwd is project root so Phase 5 can locate .env
_project_root = Path(__file__).resolve().parent.parent
if _project_root.exists():
    os.chdir(_project_root)

app = FastAPI(
    title="Quant Mutual Fund Facts API",
    description="Facts-only RAG assistant for Quant funds on Groww. No investment advice.",
    version="2.0.0",
)

@app.on_event("startup")
def _warmup():
    """Pre-load the embedding model in a background thread so /health responds immediately."""
    import logging
    import threading
    log = logging.getLogger(__name__)

    def _load():
        log.info("Warming up embedding model…")
        try:
            from phase4_retrieval_engine.embedding import get_embedding_model
            get_embedding_model()
            log.info("Embedding model ready.")
        except Exception as e:
            log.warning("Embedding model warm-up failed (will retry on first query): %s", e)

    threading.Thread(target=_load, daemon=True).start()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ────────────────────────────────────────


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question")
    active_fund: str | None = Field(None, description="Single fund (backward compat)")
    active_funds: list[str] | None = Field(None, description="Selected funds (multi-select)")
    conversation_id: str | None = Field(None, description="Conversation ID for context continuity")


class QueryResponse(BaseModel):
    answer: str = Field(..., description="Assistant response or guardrail message")
    citations: list[str] = Field(default_factory=list, description="Source URLs")
    conversation_id: str = Field(..., description="Conversation ID (returned or newly created)")


class LegacyChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class LegacyChatResponse(BaseModel):
    response: str
    citation_url: str | None = None


# ── Endpoints ────────────────────────────────────────────────────────


@app.post("/query", response_model=QueryResponse)
def post_query(request: QueryRequest) -> QueryResponse:
    """Process a user query through the RAG pipeline (Phases 2–6)."""
    try:
        funds = request.active_funds or ([request.active_fund] if request.active_fund else None)
        result = run_rag(request.query.strip(), active_funds=funds)
        conv_id = request.conversation_id or str(uuid.uuid4())
        return QueryResponse(
            answer=result["answer"],
            citations=result.get("citations", []),
            conversation_id=conv_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}") from e


@app.get("/mutual-funds")
def get_mutual_funds() -> list[str]:
    """Return list of supported mutual fund display names."""
    return FUND_DISPLAY_NAMES


@app.post("/chat", response_model=LegacyChatResponse)
def post_chat(request: LegacyChatRequest) -> LegacyChatResponse:
    """Legacy chat endpoint (backward-compatible with Phase 8 Streamlit UI)."""
    try:
        result = run_rag(request.message.strip())
        return LegacyChatResponse(
            response=result["answer"],
            citation_url=result.get("citation_url"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service error: {str(e)}") from e


@app.get("/last-updated")
def get_last_updated() -> dict:
    """Return the last successful data-refresh timestamp (written by scheduler)."""
    if not LAST_UPDATED_PATH.exists():
        return {"last_updated_utc": None, "status": "never_run"}
    try:
        data = json.loads(LAST_UPDATED_PATH.read_text(encoding="utf-8"))
        return data
    except Exception:
        return {"last_updated_utc": None, "status": "error"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
