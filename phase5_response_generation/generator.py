"""
Phase 5.2 — LLM call via Groq API.

Single call per query; API key read directly from .env file to avoid
polluting os.environ (which would break ChromaDB's Pydantic Settings).
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_project_root = Path(__file__).resolve().parent.parent

from .config import (
    GROQ_API_KEY_ENV,
    GROQ_MODEL,
    MAX_TOKENS,
    SYSTEM_PROMPT,
    TEMPERATURE,
    TOP_P,
)
from .prompt_builder import build_user_message

_cached_groq_key: str | None = None


def _read_groq_key() -> str | None:
    """
    Read GROQ_API_KEY directly from .env file(s) without touching os.environ.

    ChromaDB's Settings (Pydantic BaseSettings with extra='forbid') reads
    os.environ at import time.  If GROQ_API_KEY is present it raises a
    validation error.  So we never set it in os.environ — we read the file
    ourselves and pass the key directly to the Groq client.
    """
    global _cached_groq_key
    if _cached_groq_key:
        return _cached_groq_key

    import os
    key = os.environ.get(GROQ_API_KEY_ENV, "").strip()
    if key:
        _cached_groq_key = key
        return key

    for env_path in (_project_root / ".env", Path.cwd() / ".env"):
        if not env_path.exists():
            continue
        try:
            text = env_path.read_text(encoding="utf-8-sig", errors="ignore")
            for line in text.splitlines():
                line = line.strip().lstrip("\ufeff")
                if line.startswith("GROQ_API_KEY="):
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if value:
                        _cached_groq_key = value
                        return value
        except Exception:
            continue
    return None


_cached_client = None


def _get_client():
    """Lazy-create and cache a single Groq client (reuses HTTP connection pool)."""
    global _cached_client
    if _cached_client is not None:
        return _cached_client

    from groq import Groq

    api_key = _read_groq_key()
    if not api_key:
        logger.warning("GROQ_API_KEY missing. Set it in .env (see .env.example).")
        raise ValueError(f"Missing {GROQ_API_KEY_ENV}. Set it in .env for LLM calls.")
    _cached_client = Groq(api_key=api_key)
    return _cached_client


def generate(retrieved_context: str, user_query: str) -> str:
    """
    Single LLM call: system prompt + context + user query → raw response text.

    Uses Groq API with temperature=0, max_tokens=300, top_p=1.0.
    Raises ValueError if GROQ_API_KEY is not set.
    """
    logger.info("Groq generate: model=%s, context_len=%d", GROQ_MODEL, len(retrieved_context or ""))
    client = _get_client()
    user_content = build_user_message(retrieved_context, user_query)
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            top_p=TOP_P,
        )
    except Exception as e:
        logger.exception("Groq API call failed: %s", type(e).__name__)
        raise
    raw = response.choices[0].message.content
    return (raw or "").strip()
