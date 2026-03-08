"""
Phase 5.3 — Prompt assembly.

Builds user message: CONTEXT block + USER QUESTION.
System prompt is in config.
"""

from .config import SYSTEM_PROMPT


def build_user_message(retrieved_context: str, user_query: str) -> str:
    """
    Assemble the user-facing part of the prompt per architecture 5.3.

    Format:
      CONTEXT:
      ---
      {retrieved_context already contains chunk text + Source: url}
      ---

      USER QUESTION: {user_query}

      ANSWER:
    """
    if not retrieved_context or not retrieved_context.strip():
        return f"CONTEXT:\n(No context provided.)\n\nUSER QUESTION: {user_query}\n\nANSWER:"
    return f"CONTEXT:\n{retrieved_context.strip()}\n\nUSER QUESTION: {user_query}\n\nANSWER:"


def get_system_prompt() -> str:
    """Return the hardcoded system prompt (non-overridable)."""
    return SYSTEM_PROMPT
