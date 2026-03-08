"""
Scheduler — Daily Data Refresh (triggers Phase 1).

Runs Phase 1 pipeline daily at 6:30 PM IST then rebuilds the ChromaDB index.
Writes data/last_updated.json on success.
"""

from .job import run_daily_ingestion
from .scheduler import get_scheduler, run_scheduler

__all__ = ["run_daily_ingestion", "get_scheduler", "run_scheduler"]
