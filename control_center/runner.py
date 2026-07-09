from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

RUNTIME_DIR = REPO_ROOT / "data" / "ui_runtime"
STATE_PATH = RUNTIME_DIR / "pipeline_state.json"
LOG_PATH = RUNTIME_DIR / "pipeline.log"

LIVE_CONFIRMATION = "APPLY_LIVE"


def _now() -> str:
    return datetime.now(
        UTC,
    ).isoformat()


def _ensure_runtime_dir() -> None:
    RUNTIME_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def build_pipeline_command(
    *,
    live: bool,
    max_applications: int,
    canary: bool = False,
) -> list[str]:
    if max_applications <= 0:
        raise ValueError("max_applications must be greater than zero")

    command = [
        sys.executable,
        str(REPO_ROOT / "run_pipeline.py"),
        "--max-applications",
        str(max_applications),
    ]

    if live:
        command.extend(
            [
                "--live",
                "--confirm-live",
                LIVE_CONFIRMATION,
            ]
        )

    if live and canary:
        command.append("--canary")

    return command


def _write_state(
    payload: dict[str, Any],
) -> None:
    _ensure_runtime_dir()

    temporary = STATE_PATH.with_suffix(".json.tmp")

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary.replace(
        STATE_PATH,
    )


def read_process_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {
            "status": "IDLE",
        }

    try:
        payload = json.loads(
            STATE_PATH.read_text(
                encoding="utf-8",
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {
            "status": "IDLE",
        }

    if not isinstance(payload, dict):
        return {
            "status": "IDLE",
        }

    if payload.get("status") == "RUNNING":
        pid = payload.get("pid")

        if pid and not process_is_running(int(pid)):
            payload["status"] = (
                "SUCCESS" if payload.get("exit_code") == 0 else "UNKNOWN"
            )

    return payload


def process_is_running(
    pid: int,
) -> bool:
    try:
        os.kill(
            pid,
            0,
        )
    except OSError:
        return False

    return True


def pipeline_is_running() -> bool:
    state = read_process_state()

    if state.get("status") != "RUNNING":
        return False

    pid = state.get("pid")

    if not pid:
        return False

    return process_is_running(int(pid))


def launch_pipeline(
    *,
    live: bool,
    max_applications: int,
    canary: bool = False,
) -> dict[str, Any]:
    if pipeline_is_running():
        raise RuntimeError("A pipeline process is already running.")

    command = build_pipeline_command(
        live=live,
        max_applications=max_applications,
        canary=canary,
    )

    _ensure_runtime_dir()

    log_handle = LOG_PATH.open(
        "w",
        encoding="utf-8",
    )

    env = os.environ.copy()

    process = subprocess.Popen(
        command,
        cwd=str(REPO_ROOT),
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    state = {
        "status": "RUNNING",
        "pid": process.pid,
        "started_at": _now(),
        "completed_at": None,
        "exit_code": None,
        "live": live,
        "canary": canary,
        "max_applications": max_applications,
        "command": command,
        "log_path": str(LOG_PATH),
    }

    _write_state(state)

    return state


def refresh_process_state() -> dict[str, Any]:
    state = read_process_state()

    if state.get("status") != "RUNNING":
        return state

    pid = state.get("pid")

    if not pid:
        state["status"] = "UNKNOWN"
        _write_state(state)
        return state

    if process_is_running(int(pid)):
        return state

    state["status"] = "COMPLETED"
    state["completed_at"] = _now()

    _write_state(state)

    return state


def read_pipeline_log(
    *,
    max_characters: int = 20000,
) -> str:
    if not LOG_PATH.exists():
        return ""

    try:
        content = LOG_PATH.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return ""

    return content[-max_characters:]
