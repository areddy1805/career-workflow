from __future__ import annotations
from typing import Any
import pandas as pd
from control_center.data import (application_summary, latest_run, latest_terminal_run, run_history, read_applications, read_application_events, lifecycle_distribution, priority_distribution, subtrack_distribution, review_cases, read_manual_action_queue, safe_settings, ledger_path, runs_path, manual_queue_path, calculate_duration)
from control_center.runner import refresh_process_state, pipeline_is_running, read_pipeline_log, launch_pipeline
from control_center.manual_jobs import read_manual_jobs, add_manual_job, update_manual_job_status, MANUAL_JOB_SOURCES, MANUAL_JOB_STATUSES, MANUAL_JOBS_DB
from control_center.diagnostics import collect_health_checks, health_summary
from control_center.run_inspector import available_runs, inspect_run, read_text_artifact
from control_center.analytics_helpers import application_age_distribution, score_band_distribution, average_time_to_first_response_hours, segment_funnel
from control_center.workflows import run_reconciliation, run_application_report

def records(frame: pd.DataFrame, limit: int|None=None) -> list[dict[str,Any]]:
    if frame is None or frame.empty: return []
    f=frame.head(limit) if limit else frame
    return f.where(pd.notna(f), None).to_dict('records')

def run_count(run: dict[str,Any], key: str) -> int:
    try: return int(run.get(key, (run.get('counts') or {}).get(key,0)) or 0)
    except (TypeError,ValueError): return 0
