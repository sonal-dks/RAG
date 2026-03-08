"""
Phase 7 — Backend configuration.

Stateless API; no PII storage. Reads from vector store and env (e.g. GROQ_API_KEY).
"""

from pathlib import Path

DEFAULT_CITATION_URL = "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LAST_UPDATED_PATH = PROJECT_ROOT / "data" / "last_updated.json"

FUND_DISPLAY_NAMES: list[str] = [
    "Quant Small Cap Fund",
    "Quant Infrastructure Fund",
    "Quant Flexi Cap Fund",
    "Quant ELSS Tax Saver Fund",
    "Quant Large Cap Fund",
    "Quant ESG Integration Strategy Fund",
    "Quant Mid Cap Fund",
    "Quant Multi Cap Fund",
    "Quant Aggressive Hybrid Fund",
    "Quant Focused Fund",
]
