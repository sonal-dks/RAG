"""
Run the daily data refresh scheduler.

Usage:
    python -m scheduler.run_scheduler

Logs go to both console and logs/scheduler.log.
"""

import logging
import sys

from .config import LOG_DIR, LOG_FILE
from .scheduler import run_scheduler


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
    logging.info("Scheduler starting (logs → %s)", LOG_FILE)
    try:
        run_scheduler()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped.")
        sys.exit(0)
