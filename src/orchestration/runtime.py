from __future__ import annotations

import json
import os
import signal
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def effective_limit(*limits: int | None) -> int | None:
    bounded = [value for value in limits if value is not None]
    return min(bounded) if bounded else None


class PipelineLockError(RuntimeError):
    pass


class PipelineLock(AbstractContextManager):
    """Atomic singleton lock with conservative stale-lock recovery."""

    def __init__(self, path: str | Path = "data/ui_runtime/pipeline.lock", *, stale_after_minutes: int = 720):
        self.path = Path(path)
        self.stale_after = timedelta(minutes=stale_after_minutes)
        self.acquired = False

    def _stale(self) -> bool:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            created = datetime.fromisoformat(payload["created_at"])
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            return datetime.now(UTC) - created.astimezone(UTC) > self.stale_after
        except Exception:
            return True

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            if not self._stale():
                raise PipelineLockError(f"Pipeline already running; lock exists at {self.path}")
            self.path.unlink(missing_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        fd = os.open(self.path, flags, 0o600)
        payload = {"pid": os.getpid(), "created_at": datetime.now(UTC).isoformat()}
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        self.acquired = True

    def release(self) -> None:
        if self.acquired:
            self.path.unlink(missing_ok=True)
            self.acquired = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False


@dataclass
class CircuitBreaker:
    max_consecutive_failures: int = 5
    consecutive_failures: int = 0
    tripped: bool = False
    reason: str = ""

    def success(self) -> None:
        self.consecutive_failures = 0

    def failure(self, reason: str) -> bool:
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.max_consecutive_failures:
            self.tripped = True
            self.reason = reason
        return self.tripped
