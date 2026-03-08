"""
Scheduler configuration — daily Phase 1 run at 11:00 AM IST.
"""

from pathlib import Path

SCHEDULE_HOUR = 11
SCHEDULE_MINUTE = 0
TIMEZONE = "Asia/Kolkata"

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 60

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LAST_UPDATED_PATH = PROJECT_ROOT / "data" / "last_updated.json"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "scheduler.log"
