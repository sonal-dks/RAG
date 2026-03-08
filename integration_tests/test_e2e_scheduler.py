"""
End-to-end integration tests: Scheduler.

Verifies that the scheduler job produces the expected metadata and that
the backend can serve it.
"""

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from phase7_backend.app import app
from scheduler.config import SCHEDULE_HOUR, SCHEDULE_MINUTE, TIMEZONE
from scheduler.job import run_daily_ingestion, _write_last_updated
from scheduler.scheduler import get_scheduler


def test_e2e_scheduler_config():
    """Scheduler is configured for 6:30 PM IST."""
    assert SCHEDULE_HOUR == 18
    assert SCHEDULE_MINUTE == 30
    assert TIMEZONE == "Asia/Kolkata"


def test_e2e_scheduler_has_job():
    """APScheduler has exactly one daily ingestion job."""
    s = get_scheduler()
    jobs = s.get_jobs()
    assert len(jobs) == 1
    assert "ingestion" in jobs[0].name.lower()


def test_e2e_scheduler_writes_metadata(tmp_path):
    """After a successful run, data/last_updated.json is written with expected keys."""
    lu_path = tmp_path / "last_updated.json"
    with (
        patch("scheduler.job._run_phase1_pipeline"),
        patch("scheduler.job._run_phase4_index_build", return_value=42),
        patch("scheduler.job.LAST_UPDATED_PATH", lu_path),
        patch("scheduler.job.PROCESSED_DIR", tmp_path),
    ):
        (tmp_path / "dummy.json").touch()
        ok = run_daily_ingestion()
    assert ok is True
    assert lu_path.exists()
    data = json.loads(lu_path.read_text())
    assert data["status"] == "success"
    assert data["chunks_indexed"] == 42
    assert data["last_updated_utc"] is not None


def test_e2e_scheduler_metadata_served_by_backend(tmp_path):
    """Backend GET /last-updated serves the file the scheduler writes."""
    lu_path = tmp_path / "last_updated.json"
    _write_last_updated.__wrapped__ if hasattr(_write_last_updated, "__wrapped__") else None
    with patch("scheduler.job.LAST_UPDATED_PATH", lu_path):
        _write_last_updated(100)
    data = json.loads(lu_path.read_text())
    with patch("phase7_backend.app.LAST_UPDATED_PATH", lu_path):
        tc = TestClient(app)
        r = tc.get("/last-updated")
    assert r.status_code == 200
    resp = r.json()
    assert resp["status"] == "success"
    assert resp["chunks_indexed"] == 100
    assert resp["last_updated_utc"] == data["last_updated_utc"]
