"""
Phase 6.3 — Citation validator.

Extract source_url from response; verify against whitelist; replace if hallucinated.
"""

import re
from typing import NamedTuple

from .config import ALLOWED_URLS, CITATION_PREFIX, DEFAULT_FUND_PAGE_URL


class CitationResult(NamedTuple):
    extracted_url: str | None  # URL found in response (may be invalid)
    validated_url: str | None  # URL to use (whitelisted or fallback)
    corrected_text: str  # Response with URL fixed if needed
    was_corrected: bool


# Match "Last updated from sources: <URL>" or "Source: <URL>" or similar
_URL_IN_TEXT_PATTERN = re.compile(
    r"(?:Last\s+updated\s+from\s+sources?|Source[s]?)\s*:\s*(\S+)",
    re.IGNORECASE,
)
# Match bare URLs (http/https)
_BARE_URL_PATTERN = re.compile(r"https?://[^\s\)\]\>]+")


def _normalize_url(url: str) -> str:
    return url.rstrip(".,;:)").strip()


def validate_citation(
    response_text: str,
    fallback_url: str | None = None,
) -> CitationResult:
    """
    Extract URL from response, check against ALLOWED_URLS.
    If extracted URL not in whitelist, replace with fallback_url or default.
    """
    if not response_text or not isinstance(response_text, str):
        return CitationResult(
            extracted_url=None,
            validated_url=fallback_url or DEFAULT_FUND_PAGE_URL,
            corrected_text="",
            was_corrected=False,
        )
    text = response_text.strip()
    allowed_set = {u.rstrip("/") for u in ALLOWED_URLS}
    allowed_set |= set(ALLOWED_URLS)

    extracted = None
    for m in _URL_IN_TEXT_PATTERN.finditer(text):
        raw = _normalize_url(m.group(1))
        if raw.startswith("http"):
            extracted = raw
            break
    if not extracted and _BARE_URL_PATTERN.search(text):
        # Take last URL-like string (often the citation)
        for m in reversed(list(_BARE_URL_PATTERN.finditer(text))):
            extracted = _normalize_url(m.group(0))
            break

    if not extracted:
        validated = fallback_url or DEFAULT_FUND_PAGE_URL
        corrected = text
        if CITATION_PREFIX not in text:
            corrected = f"{text}\n\n{CITATION_PREFIX} {validated}"
        return CitationResult(
            extracted_url=None,
            validated_url=validated,
            corrected_text=corrected,
            was_corrected=validated != (extracted or ""),
        )

    # Check if extracted URL is in whitelist (exact or with/without trailing slash)
    if any(extracted == u or extracted.rstrip("/") == u.rstrip("/") for u in ALLOWED_URLS):
        return CitationResult(
            extracted_url=extracted,
            validated_url=extracted,
            corrected_text=text,
            was_corrected=False,
        )

    # Hallucinated or invalid URL — replace with fallback
    validated = fallback_url or DEFAULT_FUND_PAGE_URL
    corrected = re.sub(
        re.escape(extracted),
        validated,
        text,
        count=1,
        flags=re.IGNORECASE,
    )
    if CITATION_PREFIX not in corrected:
        corrected = f"{corrected}\n\n{CITATION_PREFIX} {validated}"
    return CitationResult(
        extracted_url=extracted,
        validated_url=validated,
        corrected_text=corrected,
        was_corrected=True,
    )
