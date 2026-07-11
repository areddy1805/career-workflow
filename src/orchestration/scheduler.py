from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[2]

@dataclass(frozen=True)
class SchedulerConfig:
    full_hour: int = 7
    incremental_interval_minutes: int = 180
    poll_seconds: int = 30
    state_path: Path = Path("data/ui_runtime/scheduler_state.json")

    @classmethod
    def from_env(cls) -> "SchedulerConfig":
        raw_path = Path(os.getenv("AUTOMATION_SCHEDULER_STATE_PATH", "data/ui_runtime/scheduler_state.json"))
        if not raw_path.is_absolute():
            raw_path = REPO_ROOT / raw_path
        return cls(
            full_hour=int(os.getenv("AUTOMATION_FULL_RUN_HOUR", "7")),
            incremental_interval_minutes=int(os.getenv("AUTOMATION_INCREMENTAL_INTERVAL_MINUTES", "180")),
            poll_seconds=int(os.getenv("AUTOMATION_POLL_SECONDS", "30")),
            state_path=raw_path,
        )

def next_mode(now: datetime, last_full: datetime | None, last_incremental: datetime | None, config: SchedulerConfig) -> str | None:
    if (last_full is None or last_full.date() < now.date()) and now.hour >= config.full_hour:
        return "full"
    if last_incremental is None or now - last_incremental >= timedelta(minutes=config.incremental_interval_minutes):
        return "incremental"
    return None

def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None

def read_scheduler_state(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def _load_state(path: Path) -> tuple[datetime | None, datetime | None]:
    payload = read_scheduler_state(path)
    return _parse(payload.get("last_full")), _parse(payload.get("last_incremental"))

def _save_state(path: Path, *, last_full: datetime | None, last_incremental: datetime | None, status: str, last_mode: str | None = None, returncode: int | None = None, error: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps({
        "status": status,
        "last_full": last_full.isoformat() if last_full else None,
        "last_incremental": last_incremental.isoformat() if last_incremental else None,
        "last_mode": last_mode,
        "last_returncode": returncode,
        "last_error": error,
        "updated_at": datetime.now().astimezone().isoformat(),
    }, indent=2), encoding="utf-8")
    temporary.replace(path)

def run_scheduler(config: SchedulerConfig | None = None, *, sleep_fn: Callable[[float], None] = time.sleep) -> None:
    config = config or SchedulerConfig.from_env()
    last_full, last_incremental = _load_state(config.state_path)
    _save_state(config.state_path, last_full=last_full, last_incremental=last_incremental, status="IDLE")
    try:
        while True:
            now = datetime.now().astimezone()
            mode = next_mode(now, last_full, last_incremental, config)
            if mode:
                _save_state(config.state_path, last_full=last_full, last_incremental=last_incremental, status="RUNNING", last_mode=mode)
                command = [sys.executable, str(REPO_ROOT / "run_pipeline.py"), "--live", "--confirm-live", "APPLY_LIVE", "--acquisition-mode", mode]
                try:
                    completed = subprocess.run(command, cwd=str(REPO_ROOT), check=False)
                    if completed.returncode == 0:
                        if mode == "full":
                            last_full = now
                        last_incremental = now
                        status, error = "SUCCESS", ""
                    else:
                        status, error = "FAILED", f"pipeline exit code {completed.returncode}"
                    _save_state(config.state_path, last_full=last_full, last_incremental=last_incremental, status=status, last_mode=mode, returncode=completed.returncode, error=error)
                except Exception as exc:
                    _save_state(config.state_path, last_full=last_full, last_incremental=last_incremental, status="FAILED", last_mode=mode, error=f"{type(exc).__name__}: {exc}")
            sleep_fn(config.poll_seconds)
    except KeyboardInterrupt:
        _save_state(config.state_path, last_full=last_full, last_incremental=last_incremental, status="STOPPED")
