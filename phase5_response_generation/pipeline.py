"""
Phase 5 — Response Generation pipeline.

Input: user query + retrieved context (and optional sufficient flag) from Phase 4.
Output: raw LLM response (or pass-through when context insufficient).
Single LLM call per user query.
"""

import logging

from .config import GROQ_API_KEY_ENV, GROQ_MODEL
from .generator import generate

logger = logging.getLogger(__name__)

# Message used by Phase 4 when no chunks meet threshold
INSUFFICIENT_CONTEXT_MARKER = "I don't have enough information to answer that."

# Shown when GROQ_API_KEY is missing so the user can fix .env
MISSING_KEY_MESSAGE = (
    "Answer generation is not configured. Set GROQ_API_KEY in the project .env file (see .env.example) and restart the backend."
)


def process_query(
    user_query: str,
    retrieved_context: str,
    *,
    sufficient: bool = True,
) -> dict:
    """
    Generate factual, cited answer from Phase 4 context using a single Groq call.

    If context is insufficient (empty or equals Phase 4's insufficient message,
    or sufficient=False), no LLM call is made; the insufficient message is
    returned as raw_response.

    Returns:
      - raw_response: str — LLM output or insufficient-info message
      - model_used: str | None — Groq model name if LLM was called, else None
      - api_called: bool — True if Groq API was invoked
    """
    if not user_query or not isinstance(user_query, str):
        return {
            "raw_response": INSUFFICIENT_CONTEXT_MARKER,
            "model_used": None,
            "api_called": False,
        }
    query = user_query.strip()
    if not query:
        return {
            "raw_response": INSUFFICIENT_CONTEXT_MARKER,
            "model_used": None,
            "api_called": False,
        }

    # No LLM call when context is insufficient
    context_empty = not (retrieved_context and retrieved_context.strip())
    context_insufficient = (
        retrieved_context and retrieved_context.strip() == INSUFFICIENT_CONTEXT_MARKER
    )
    if not sufficient or context_empty or context_insufficient:
        return {
            "raw_response": INSUFFICIENT_CONTEXT_MARKER,
            "model_used": None,
            "api_called": False,
        }

    try:
        raw = generate(retrieved_context, query)
        return {
            "raw_response": raw,
            "model_used": GROQ_MODEL,
            "api_called": True,
        }
    except ValueError as e:
        if GROQ_API_KEY_ENV in str(e):
            logger.warning("Groq skipped (missing or empty API key): %s", e)
            return {
                "raw_response": MISSING_KEY_MESSAGE,
                "model_used": None,
                "api_called": False,
            }
        raise
    except Exception as e:
        logger.exception("Groq pipeline failed: %s - %s", type(e).__name__, e)
        return {
            "raw_response": "Service temporarily unavailable. Please try again later.",
            "model_used": None,
            "api_called": False,
        }
