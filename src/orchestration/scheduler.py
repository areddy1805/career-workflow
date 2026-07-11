from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class SchedulerConfig:
    full_hour: int = 7
    incremental_interval_minutes: int = 180
    poll_seconds: int = 30
    state_path: Path = Path("data/ui_runtime/scheduler_state.json")

    @classmethod
    def from_env(cls) -> "SchedulerConfig":
        return cls(
            full_hour=int(os.getenv("AUTOMATION_FULL_RUN_HOUR", "7")),
            incremental_interval_minutes=int(os.getenv("AUTOMATION_INCREMENTAL_INTERVAL_MINUTES", "180")),
            poll_seconds=int(os.getenv("AUTOMATION_POLL_SECONDS", "30")),
            state_path=Path(os.getenv("AUTOMATION_SCHEDULER_STATE_PATH", "data/ui_runtime/scheduler_state.json")),
        )


def next_mode(now: datetime, last_full: datetime | None, last_incremental: datetime | None, config: SchedulerConfig) -> str | None:
    if (last_full is None or last_full.date() < now.date()) and now.hour >= config.full_hour:
        return "full"
    if last_incremental is None or now - last_incremental >= timedelta(minutes=config.incremental_interval_minutes):
        return "incremental"
    return None


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _load_state(path: Path) -> tuple[datetime | None, datetime | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return _parse(payload.get("last_full")), _parse(payload.get("last_incremental"))
    except Exception:
        return None, None


def _save_state(path: Path, last_full: datetime | None, last_incremental: datetime | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps({
        "last_full": last_full.isoformat() if last_full else None,
        "last_incremental": last_incremental.isoformat() if last_incremental else None,
        "updated_at": datetime.now().astimezone().isoformat(),
    }, indent=2), encoding="utf-8")
    temporary.replace(path)


def run_scheduler(config: SchedulerConfig | None = None) -> None:
    config = config or SchedulerConfig.from_env()
    last_full, last_incremental = _load_state(config.state_path)
    try:
        while True:
            now = datetime.now().astimezone()
            mode = next_mode(now, last_full, last_incremental, config)
            if mode:
                command = [sys.executable, "run_pipeline.py", "--live", "--confirm-live", "APPLY_LIVE", "--acquisition-mode", mode]
                completed = subprocess.run(command, check=False)
                if completed.returncode == 0:
                    if mode == "full":
                        last_full = now
                    last_incremental = now
                    _save_state(config.state_path, last_full, last_incremental)
            time.sleep(config.poll_seconds)
    except KeyboardInterrupt:
        return
