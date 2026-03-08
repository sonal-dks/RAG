"""
APScheduler setup: daily job at configured time (default 6:30 PM IST).
"""

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import SCHEDULE_HOUR, SCHEDULE_MINUTE, TIMEZONE
from .job import run_daily_ingestion

logger = logging.getLogger(__name__)


def get_scheduler() -> BlockingScheduler:
    tz = ZoneInfo(TIMEZONE)
    scheduler = BlockingScheduler(timezone=tz)
    scheduler.add_job(
        run_daily_ingestion,
        trigger=CronTrigger(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE),
        id="daily_phase1_ingestion",
        name="Daily Phase 1 ingestion + index build",
        replace_existing=True,
    )
    logger.info(
        "Scheduled daily ingestion at %02d:%02d %s",
        SCHEDULE_HOUR,
        SCHEDULE_MINUTE,
        TIMEZONE,
    )
    return scheduler


def run_scheduler() -> None:
    s = get_scheduler()
    s.start()
