from __future__ import annotations

from typing import Any

import pandas as pd

from control_center.data import (
    application_summary,
    calculate_duration,
    latest_run,
    latest_terminal_run,
    ledger_path,
    lifecycle_distribution,
    manual_queue_path,
    priority_distribution,
    read_application_events,
    read_applications,
    read_manual_action_queue,
    review_cases,
    runs_path,
    safe_settings,
    subtrack_distribution,
    run_history,
)
from control_center.runner import (
    launch_pipeline,
    pipeline_is_running,
    read_pipeline_log,
    refresh_process_state,
)
from control_center.manual_jobs import (
    MANUAL_JOB_SOURCES,
    MANUAL_JOB_STATUSES,
    MANUAL_JOBS_DB,
    add_manual_job,
    read_manual_jobs,
    update_manual_job_status,
)
from control_center.diagnostics import collect_health_checks, health_summary
from control_center.run_inspector import available_runs, inspect_run, read_text_artifact
from control_center.analytics_helpers import (
    application_age_distribution,
    average_time_to_first_response_hours,
    run_outcome_totals,
    score_band_distribution,
    segment_funnel,
)
from control_center.workflows import run_reconciliation, run_application_report
from src.application.manual_action_queue import ManualActionQueue, QUEUE_STATUSES
from src.application.workflow import WorkflowStatus
from src.application.workflow_queue import WorkflowQueue
from src.application.queue_analytics import QueueAnalyticsService
from src.orchestration.scheduler import SchedulerConfig, read_scheduler_state

WORKFLOW_STATUSES: list[str] = [s.value for s in WorkflowStatus]


def records(frame: pd.DataFrame, limit: int | None = None) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    f = frame.head(limit) if limit else frame
    return f.where(pd.notna(f), None).to_dict("records")


def run_count(run: dict[str, Any], key: str) -> int:
    try:
        return int(run.get(key, (run.get("counts") or {}).get(key, 0)) or 0)
    except (TypeError, ValueError):
        return 0


def update_external_action_status(job_id: str, status: str, note: str = "") -> bool:
    return ManualActionQueue(manual_queue_path()).update_status(job_id, status, note=note)


def scheduler_state() -> dict[str, Any]:
    config = SchedulerConfig.from_env()
    state = read_scheduler_state(config.state_path)
    state["state_path"] = str(config.state_path)
    return state


# ---------------------------------------------------------------------------
# Workflow queue services
# ---------------------------------------------------------------------------


def get_workflow_queue() -> WorkflowQueue:
    """Return a WorkflowQueue bound to the configured paths."""
    return WorkflowQueue(
        maq_path=manual_queue_path(),
    )


def get_queue_analytics(queue: WorkflowQueue | None = None) -> QueueAnalyticsService:
    """Return a QueueAnalyticsService for the given (or default) queue."""
    return QueueAnalyticsService(queue or get_workflow_queue())


def workflow_queue_transition(
    job_id: str,
    to_status: WorkflowStatus,
    *,
    actor: str = "user",
    note: str = "",
) -> bool:
    return get_workflow_queue().transition(
        job_id, to_status, actor=actor, note=note
    )


def workflow_queue_add_note(
    job_id: str, text: str, *, author: str = "user"
) -> bool:
    return get_workflow_queue().add_note(job_id, text, author=author)


def workflow_queue_retry(job_id: str) -> bool:
    return get_workflow_queue().retry(job_id, actor="user")
