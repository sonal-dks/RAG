"""
Phase 6.4 — Response formatter.

Enforce 5-sentence cap; append citation line if missing.
"""

import re
from .config import CITATION_PREFIX, MAX_SENTENCES


def _sentence_split(text: str) -> list[str]:
    """Split on sentence boundaries (. ? !) and return non-empty sentences."""
    if not text or not text.strip():
        return []
    # Split on . ? ! but keep trailing newlines/spaces minimal
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def format_response(text: str, citation_url: str | None = None) -> str:
    """
    Enforce MAX_SENTENCES cap (truncate gracefully).
    For multi-fund responses (sections separated by blank lines with **Fund:**
    headers), the cap is applied per section so each fund keeps its answer.
    Strip any "Last updated from sources: ..." line the LLM may have generated.
    """
    if not text or not isinstance(text, str):
        return ""
    t = text.strip()
    if not t:
        return ""

    # Remove any "Last updated from sources: ..." line the LLM added
    lines = t.split("\n")
    lines = [ln for ln in lines if not ln.strip().lower().startswith("last updated from sources")]
    t = "\n".join(lines).strip()

    # Multi-fund response: apply sentence cap per section
    if "\n\n**" in t:
        sections = re.split(r"\n\n(?=\*\*)", t)
        capped = []
        for section in sections:
            s = section.strip()
            if not s:
                continue
            sentences = _sentence_split(s)
            if len(sentences) > MAX_SENTENCES:
                s = " ".join(sentences[:MAX_SENTENCES])
            capped.append(s.strip())
        return "\n\n".join(capped)

    sentences = _sentence_split(t)
    if len(sentences) > MAX_SENTENCES:
        t = " ".join(sentences[:MAX_SENTENCES])

    return t.strip()
