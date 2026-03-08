"""
Phase 2.1 — PII Detector.

Regex-based detection for PAN, Aadhaar, phone numbers, email, bank account patterns.
Query is not forwarded if PII is detected.
"""

import re
from typing import NamedTuple


class PIIResult(NamedTuple):
    """Result of PII check."""

    detected: bool
    kind: str | None  # e.g. "pan", "aadhaar", "phone", "email", "bank"


# PAN: 5 letters + 4 digits + 1 letter (e.g. ABCDE1234F)
_PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)

# Aadhaar: 4 digits optional space, repeated 3 times (e.g. 1234 5678 9012 or 123456789012)
_AADHAAR_PATTERN = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")

# Indian phone: 10 digits, optional +91, optional spaces/dashes
_PHONE_PATTERN = re.compile(
    r"(?:\+91[\s-]*)?[6-9]\d{9}\b|(?:\+91[\s-]*)?[6-9]\d[\s-]?\d{4}[\s-]?\d{4}"
)

# Email: standard pattern
_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# Bank account: 9–18 digits (Indian bank account numbers)
_BANK_ACCOUNT_PATTERN = re.compile(r"\b\d{9,18}\b")

# OTP: 4–8 digit code often typed by users
_OTP_PATTERN = re.compile(r"\b(?:OTP|otp)[\s:]*\d{4,8}\b", re.IGNORECASE)


def check_pii(text: str) -> PIIResult:
    """
    Check if the input text contains PII (PAN, Aadhaar, phone, email, bank, OTP).

    Returns PIIResult(detected=True, kind="...") if PII found, else PIIResult(False, None).
    """
    if not text or not isinstance(text, str):
        return PIIResult(False, None)

    t = text.strip()
    if not t:
        return PIIResult(False, None)

    if _PAN_PATTERN.search(t):
        return PIIResult(True, "pan")
    if _AADHAAR_PATTERN.search(t):
        return PIIResult(True, "aadhaar")
    if _OTP_PATTERN.search(t):
        return PIIResult(True, "otp")
    if _PHONE_PATTERN.search(t):
        return PIIResult(True, "phone")
    if _EMAIL_PATTERN.search(t):
        return PIIResult(True, "email")
    if _BANK_ACCOUNT_PATTERN.search(t) and _looks_like_bank_context(t):
        return PIIResult(True, "bank")

    return PIIResult(False, None)


def _looks_like_bank_context(text: str) -> bool:
    """Reduce false positives: long digit strings only as PII if bank-like context."""
    lower = text.lower()
    return any(
        word in lower
        for word in ("account", "bank", "ifsc", "upi", "transfer", "rtgs", "neft")
    )
