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
EXIT_PATH = RUNTIME_DIR / "pipeline_exit.json"
LIVE_CONFIRMATION = "APPLY_LIVE"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _ensure_runtime_dir() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def build_pipeline_command(*, live: bool, max_applications: int, canary: bool = False) -> list[str]:
    if max_applications <= 0:
        raise ValueError("max_applications must be greater than zero")
    command = [sys.executable, str(REPO_ROOT / "run_pipeline.py"), "--max-applications", str(max_applications)]
    if live:
        command.extend(["--live", "--confirm-live", LIVE_CONFIRMATION])
    if live and canary:
        command.append("--canary")
    return command


def _write_state(payload: dict[str, Any]) -> None:
    _ensure_runtime_dir()
    temporary = STATE_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(STATE_PATH)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def process_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def read_process_state() -> dict[str, Any]:
    state = _read_json(STATE_PATH)
    if not state:
        return {"status": "IDLE"}
    exit_payload = _read_json(EXIT_PATH)
    if state.get("status") == "RUNNING" and exit_payload.get("launcher_pid") == state.get("pid"):
        state["status"] = "SUCCESS" if exit_payload.get("exit_code") == 0 else "FAILED"
        state["exit_code"] = exit_payload.get("exit_code")
        state["completed_at"] = exit_payload.get("completed_at")
        _write_state(state)
    elif state.get("status") == "RUNNING" and state.get("pid") and not process_is_running(int(state["pid"])):
        state["status"] = "UNKNOWN"
        state["completed_at"] = _now()
        _write_state(state)
    return state


def pipeline_is_running() -> bool:
    state = read_process_state()
    return state.get("status") == "RUNNING" and bool(state.get("pid")) and process_is_running(int(state["pid"]))


def launch_pipeline(*, live: bool, max_applications: int, canary: bool = False) -> dict[str, Any]:
    if pipeline_is_running():
        raise RuntimeError("A pipeline process is already running.")
    command = build_pipeline_command(live=live, max_applications=max_applications, canary=canary)
    _ensure_runtime_dir()
    EXIT_PATH.unlink(missing_ok=True)
    wrapper = [
        sys.executable,
        str(REPO_ROOT / "control_center" / "process_wrapper.py"),
        str(EXIT_PATH),
        str(LOG_PATH),
        *command,
    ]
    process = subprocess.Popen(
        wrapper,
        cwd=str(REPO_ROOT),
        env=os.environ.copy(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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
    return read_process_state()


def read_pipeline_log(*, max_characters: int = 20000) -> str:
    if not LOG_PATH.exists():
        return ""
    try:
        return LOG_PATH.read_text(encoding="utf-8", errors="replace")[-max_characters:]
    except OSError:
        return ""
