"""
Tests for the daily ingestion scheduler.

Covers: config, scheduler setup, job execution, last_updated.json writing,
retry logic, and logging.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from scheduler.config import (
    SCHEDULE_HOUR,
    SCHEDULE_MINUTE,
    TIMEZONE,
    LAST_UPDATED_PATH,
    LOG_DIR,
    LOG_FILE,
    MAX_RETRIES,
)
from scheduler.job import run_daily_ingestion, _write_last_updated
from scheduler.scheduler import get_scheduler


class TestSchedulerConfig:
    def test_schedule_time_is_6_30_pm(self):
        assert SCHEDULE_HOUR == 18
        assert SCHEDULE_MINUTE == 30

    def test_timezone_ist(self):
        assert TIMEZONE == "Asia/Kolkata"

    def test_last_updated_path_exists(self):
        assert LAST_UPDATED_PATH is not None
        assert str(LAST_UPDATED_PATH).endswith("data/last_updated.json")

    def test_log_paths_configured(self):
        assert LOG_DIR is not None
        assert LOG_FILE is not None
        assert str(LOG_FILE).endswith("scheduler.log")

    def test_max_retries(self):
        assert MAX_RETRIES >= 1


class TestGetScheduler:
    def test_returns_scheduler_with_daily_job(self):
        s = get_scheduler()
        jobs = s.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "daily_phase1_ingestion"
        assert "Daily" in jobs[0].name


class TestRunDailyIngestion:
    @patch("scheduler.job._run_phase4_index_build")
    @patch("scheduler.job._run_phase1_pipeline")
    def test_success_returns_true(self, mock_phase1, mock_phase4, tmp_path):
        mock_phase4.return_value = 42
        with patch("scheduler.job.LAST_UPDATED_PATH", tmp_path / "last_updated.json"):
            with patch("scheduler.job.PROCESSED_DIR", tmp_path):
                (tmp_path / "dummy.json").touch()
                result = run_daily_ingestion()
        assert result is True
        mock_phase1.assert_called_once()
        mock_phase4.assert_called_once()

    @patch("time.sleep")
    @patch("scheduler.job._run_phase4_index_build")
    @patch("scheduler.job._run_phase1_pipeline")
    def test_retries_on_failure(self, mock_phase1, mock_phase4, mock_sleep):
        mock_phase1.side_effect = RuntimeError("scrape failed")
        result = run_daily_ingestion()
        assert result is False
        assert mock_phase1.call_count == MAX_RETRIES + 1

    @patch("scheduler.job._run_phase4_index_build")
    @patch("scheduler.job._run_phase1_pipeline")
    def test_writes_last_updated_on_success(self, mock_phase1, mock_phase4, tmp_path):
        mock_phase4.return_value = 10
        lu_path = tmp_path / "last_updated.json"
        with patch("scheduler.job.LAST_UPDATED_PATH", lu_path):
            with patch("scheduler.job.PROCESSED_DIR", tmp_path):
                (tmp_path / "dummy.json").touch()
                run_daily_ingestion()
        assert lu_path.exists()
        data = json.loads(lu_path.read_text())
        assert data["status"] == "success"
        assert data["chunks_indexed"] == 10
        assert data["last_updated_utc"] is not None


class TestWriteLastUpdated:
    def test_creates_file(self, tmp_path):
        path = tmp_path / "last_updated.json"
        with patch("scheduler.job.LAST_UPDATED_PATH", path):
            _write_last_updated(100)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["chunks_indexed"] == 100
        assert data["status"] == "success"
        assert "last_updated_utc" in data
