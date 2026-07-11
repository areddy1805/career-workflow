from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class PipelineContext:
    run_id: str
    dry_run: bool
    max_applications: int | None

    started_at: datetime = field(default_factory=utc_now)

    # Runtime dependencies
    login_client: Any | None = None
    job_client: Any | None = None
    questionnaire_resolver: Any | None = None
    ledger: Any | None = None

    acquisition_mode: str = "full"

    # Acquisition
    acquired_jobs: list[Any] = field(default_factory=list)
    fetch_result: Any | None = None

    # Classification
    classified_jobs: list[dict[str, Any]] = field(default_factory=list)
    score_map: dict[str, dict[str, Any]] = field(default_factory=dict)
    detail_cache: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Selection
    selected_jobs: list[Any] = field(default_factory=list)
    adaptive_strategy: Any | None = None
    applied_job_ids: set[str] = field(default_factory=set)

    # Application
    application_summary: Any | None = None
    application_results: list[Any] = field(default_factory=list)
    ledger_run_id: str | None = None

    # Reconciliation
    server_history: list[Any] = field(default_factory=list)
    reconciliation_changes: int = 0

    # Strategy/report
    updated_strategy: Any | None = None
    report_snapshot: dict[str, Any] = field(default_factory=dict)

    # Generic stage state
    stage_results: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def record_error(
        self,
        *,
        stage: str,
        error: Exception,
        fatal: bool = False,
    ) -> None:
        self.errors.append(
            {
                "stage": stage,
                "type": type(error).__name__,
                "message": str(error),
                "fatal": fatal,
                "recorded_at": utc_now().isoformat(),
            }
        )
