# Production operations

## Runtime model

The pipeline remains the single execution engine. NiceGUI launches explicit interactive runs through the same `run_pipeline.py` entry point. The scheduler invokes that entry point for unattended full and incremental acquisition. `PipelineLock` prevents concurrent pipeline ownership.

## Required environment

Use a dedicated virtual environment and populate `.env` from `.env.example`. Live automation requires `APPLICATION_DRY_RUN=false`; interactive live execution still requires the CLI confirmation token. Keep secrets only in `.env` and never commit it.

## Foreground validation

Run `python run_nicegui.py` and `python run_scheduler.py` in separate terminals. Confirm `data/ui_runtime/scheduler_state.json` updates and a scheduled pipeline artifact reaches a terminal status.

## macOS service installation

Copy the plist examples from `deploy/macos` to `~/Library/LaunchAgents`, replacing `REPLACE_PYTHON` with the virtualenv Python absolute path and `REPLACE_REPO` with the repository absolute path. Create `logs/`, then load with `launchctl bootstrap gui/$(id -u) <plist>`. Inspect with `launchctl print gui/$(id -u)/com.careerworkflow.scheduler` and the log files.

## Recovery

A pipeline lock older than the configured stale threshold can be recovered by the runtime. Do not delete a fresh lock while its PID is active. Scheduler failures are recorded in scheduler state and retried on the next poll because timestamps advance only after successful pipeline completion.

## Backup

Back up `data/application_ledger.db`, `data/manual_jobs.db`, `data/manual_action_queue.json`, and `artifacts/runs`. These contain operational history and workflow state.
