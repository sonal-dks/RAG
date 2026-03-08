# Scheduler — Daily Data Refresh

Runs the Phase 1 pipeline **daily at 6:30 PM IST** so the vector store and fund data stay current with the 10 Groww scheme pages.

## What it does

1. **Phase 1:** Scrape → parse → store (all 10 funds; raw HTML + processed JSON).
2. **Phase 4:** Rebuild ChromaDB index from `data/processed/*.json`.
3. **Writes** `data/last_updated.json` with the completion timestamp and chunk count.

On failure, the job retries up to **2** times (configurable in `scheduler/config.py`).

## Run the scheduler (daily at 6:30 PM IST)

```bash
python -m scheduler.run_scheduler
```

Blocks and runs the ingestion job every day at 18:30 Asia/Kolkata. Stop with Ctrl+C.

## Run the job once (manual refresh / testing)

```bash
python -m scheduler.run_once
```

Exits 0 on success, 1 on failure (after retries).

## Logs

All runs log to **both console and `logs/scheduler.log`**. Check the log file to verify whether the scheduler has run:

```bash
cat logs/scheduler.log
```

## GitHub Actions (automated daily run)

The workflow `.github/workflows/daily-data-refresh.yml` runs the scheduler job once at **6:30 PM IST (1:00 PM UTC)** every day. It:
- Installs dependencies and Playwright
- Runs `python -m scheduler.run_once`
- Uploads `logs/scheduler.log` and `data/last_updated.json` as artifacts
- Commits updated data back to the repo

**Required secret:** `GROQ_API_KEY` — set this in GitHub repo Settings → Secrets.

You can also trigger a manual run from the Actions tab (`workflow_dispatch`).

## Configuration

Edit `scheduler/config.py`:

- **SCHEDULE_HOUR**, **SCHEDULE_MINUTE** — daily run time (default 18, 30 = 6:30 PM).
- **TIMEZONE** — timezone for the schedule (default `Asia/Kolkata`).
- **MAX_RETRIES**, **RETRY_DELAY_SECONDS** — failure handling.

## Requirements

- Phase 1 and Phase 4 dependencies (playwright, chromadb, sentence-transformers, etc.).
- `apscheduler` (see `requirements.txt`).
