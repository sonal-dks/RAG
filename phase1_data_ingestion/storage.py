"""Save parsed fund data to structured JSON files."""

import json
import logging
import time
from pathlib import Path

from .config import PROCESSED_DIR

logger = logging.getLogger(__name__)


def save_fund_data(fund_data: dict) -> Path:
    """
    Write a single fund's structured data to data/processed/<fund_key>.json.
    Returns the output path.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    fund_key = fund_data.get("fund_key", "unknown")
    fund_data["scraped_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    out_path = PROCESSED_DIR / f"{fund_key}.json"
    out_path.write_text(json.dumps(fund_data, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info("Saved processed data → %s", out_path)
    return out_path


def save_all_funds(all_fund_data: list[dict]) -> Path:
    """
    Write the combined data for all funds to data/processed/all_funds.json.
    Returns the output path.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "fund_count": len(all_fund_data),
        "funds": all_fund_data,
    }

    out_path = PROCESSED_DIR / "all_funds.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info("Saved combined data (%d funds) → %s", len(all_fund_data), out_path)
    return out_path
