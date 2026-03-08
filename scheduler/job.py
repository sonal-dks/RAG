"""
Daily ingestion job: run Phase 1 (scrape → parse → store), rebuild ChromaDB index,
and write data/last_updated.json with the completion timestamp.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .config import MAX_RETRIES, PROCESSED_DIR, RETRY_DELAY_SECONDS, LAST_UPDATED_PATH

logger = logging.getLogger(__name__)


def _run_phase1_pipeline() -> None:
    from phase1_data_ingestion.run_ingestion import run_full_pipeline
    asyncio.run(run_full_pipeline())


def _run_phase4_index_build(processed_dir: Path) -> int:
    from phase4_retrieval_engine.pipeline import build_index_from_processed_dir
    return build_index_from_processed_dir(processed_dir)


def _write_last_updated(num_chunks: int) -> None:
    """Write a metadata file recording the last successful data refresh."""
    from zoneinfo import ZoneInfo
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now.astimezone(ZoneInfo("Asia/Kolkata"))
    payload = {
        "last_updated_utc": utc_now.isoformat(timespec="seconds"),
        "last_updated_ist": ist_now.isoformat(timespec="seconds"),
        "chunks_indexed": num_chunks,
        "status": "success",
    }
    LAST_UPDATED_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_UPDATED_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Wrote last_updated metadata → %s", LAST_UPDATED_PATH)


def run_daily_ingestion() -> bool:
    """
    Run Phase 1 pipeline then rebuild vector store index.
    On success, writes data/last_updated.json.
    Returns True on success, False on failure after retries.
    """
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt > 0:
                logger.info("Retry %s/%s after %s seconds", attempt, MAX_RETRIES, RETRY_DELAY_SECONDS)
                import time
                time.sleep(RETRY_DELAY_SECONDS)
            logger.info("=== Starting daily ingestion (attempt %s/%s) ===", attempt + 1, MAX_RETRIES + 1)
            _run_phase1_pipeline()
            logger.info("Phase 1 pipeline completed successfully.")
            if not PROCESSED_DIR.exists():
                logger.warning("Processed dir %s missing after Phase 1; skipping index build", PROCESSED_DIR)
                _write_last_updated(0)
                return True
            n = _run_phase4_index_build(PROCESSED_DIR)
            logger.info("Phase 4 index build completed. Indexed %s chunks.", n)
            _write_last_updated(n)
            logger.info("=== Daily ingestion finished successfully ===")
            return True
        except Exception as e:
            last_error = e
            logger.exception("Daily ingestion failed (attempt %s/%s): %s", attempt + 1, MAX_RETRIES + 1, e)
    logger.error("Daily ingestion failed after %s attempts. Last error: %s", MAX_RETRIES + 1, last_error)
    return False
