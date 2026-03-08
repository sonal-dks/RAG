"""
Run the daily ingestion job once (Phase 1 + index build).
Useful for testing, manual refresh, or GitHub Actions.

Usage:
    python -m scheduler.run_once

Logs go to both console and logs/scheduler.log.
"""

import logging
import sys

from .config import LOG_DIR, LOG_FILE
from .job import run_daily_ingestion


def _setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    root.addHandler(fh)


if __name__ == "__main__":
    _setup_logging()
    logging.info("=== Manual / one-time ingestion run (logs → %s) ===", LOG_FILE)
    ok = run_daily_ingestion()
    if ok:
        logging.info("=== Ingestion succeeded ===")
    else:
        logging.error("=== Ingestion FAILED ===")
    sys.exit(0 if ok else 1)
