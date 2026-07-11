# Unattended automation

The pipeline is uncapped by default. `--max-applications N` is an explicit temporary bound; `--canary` forces one live attempt.

## Validation sequence

```bash
python run_pipeline.py --max-applications 20 --acquisition-mode incremental
python run_pipeline.py --live --canary --confirm-live APPLY_LIVE --acquisition-mode incremental
python run_pipeline.py --live --max-applications 5 --confirm-live APPLY_LIVE --acquisition-mode incremental
python run_pipeline.py --live --confirm-live APPLY_LIVE --acquisition-mode full
```

## Scheduler

```bash
export LIVE_APPLICATION_CONFIRMATION=APPLY_LIVE
python run_scheduler.py
```

Configuration: `AUTOMATION_FULL_RUN_HOUR`, `AUTOMATION_INCREMENTAL_INTERVAL_MINUTES`, `AUTOMATION_POLL_SECONDS`, `PIPELINE_LOCK_PATH`, `PIPELINE_LOCK_STALE_MINUTES`, `APPLICATION_MAX_CONSECUTIVE_FAILURES`, `SEARCH_MIN_NEW_JOBS_PER_PAGE`, `SEARCH_LOW_YIELD_PATIENCE`, and `SEARCH_REQUEST_DELAY_SECONDS`.

The scheduler persists successful run timestamps under `data/ui_runtime`, which should remain ignored. Pipeline locking prevents overlapping scheduler, CLI, and UI launches. Full mode uses the broad search matrix. Incremental mode defaults to fewer experience bands and one page per query while preserving all search tracks.
