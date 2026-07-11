from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

from control_center.data import ledger_path, manual_queue_path, runs_path
from control_center.manual_jobs import MANUAL_JOBS_DB
from control_center.runner import REPO_ROOT
from src.orchestration.scheduler import SchedulerConfig, read_scheduler_state


def _path_check(name: str, path: Path, *, required: bool) -> dict[str, Any]:
    exists = path.exists()
    return {
        "check": name,
        "status": "PASS" if exists or not required else "FAIL",
        "detail": str(path),
        "required": required,
    }


def collect_health_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    checks.append({
        "check": "Python",
        "status": "PASS",
        "detail": sys.version.split()[0],
        "required": True,
    })

    checks.append({
        "check": "NiceGUI package",
        "status": "PASS" if importlib.util.find_spec("nicegui") else "FAIL",
        "detail": "installed" if importlib.util.find_spec("nicegui") else "missing",
        "required": True,
    })

    checks.append(_path_check(
        "Pipeline entry point",
        REPO_ROOT / "run_pipeline.py",
        required=True,
    ))
    checks.append(_path_check(
        "Application ledger",
        ledger_path(),
        required=False,
    ))
    checks.append(_path_check(
        "Run artifacts",
        runs_path(),
        required=False,
    ))
    checks.append(_path_check(
        "External action queue",
        manual_queue_path(),
        required=False,
    ))
    checks.append(_path_check(
        "Manual jobs database",
        MANUAL_JOBS_DB,
        required=False,
    ))

    checks.append({
        "check": "Working directory",
        "status": "PASS" if Path.cwd().resolve() == REPO_ROOT.resolve() else "WARN",
        "detail": str(Path.cwd().resolve()),
        "required": False,
    })

    scheduler_config = SchedulerConfig.from_env()
    scheduler_state = read_scheduler_state(scheduler_config.state_path)
    checks.append({
        "check": "Scheduler state",
        "status": "PASS" if scheduler_state else "WARN",
        "detail": str(scheduler_config.state_path),
        "required": False,
    })

    checks.append({
        "check": "Dry-run environment",
        "status": "PASS",
        "detail": os.getenv("APPLICATION_DRY_RUN", "default"),
        "required": False,
    })

    return checks


def health_summary(checks: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "pass": sum(1 for item in checks if item["status"] == "PASS"),
        "warn": sum(1 for item in checks if item["status"] == "WARN"),
        "fail": sum(1 for item in checks if item["status"] == "FAIL"),
        "total": len(checks),
    }


def required_health_ok(checks: list[dict[str, Any]]) -> bool:
    return not any(
        item["required"] and item["status"] == "FAIL"
        for item in checks
    )
