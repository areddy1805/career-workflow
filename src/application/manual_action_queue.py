from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ManualActionQueue:
    def __init__(
        self,
        path: str | Path,
    ) -> None:
        self.path = Path(path)

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []

        try:
            payload = json.loads(
                self.path.read_text(
                    encoding="utf-8",
                )
            )
        except (
            json.JSONDecodeError,
            OSError,
        ):
            return []

        if not isinstance(payload, list):
            return []

        return payload

    def _save(
        self,
        rows: list[dict],
    ) -> None:
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")

        temporary.write_text(
            json.dumps(
                rows,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )

        temporary.replace(
            self.path,
        )

    @staticmethod
    def _value(
        job: Any,
        key: str,
        default=None,
    ):
        if isinstance(job, dict):
            return job.get(
                key,
                default,
            )

        return getattr(
            job,
            key,
            default,
        )

    def enqueue_external_apply(
        self,
        *,
        job: Any,
        score: int,
        reason: str = "",
        run_id: str = "",
    ) -> bool:
        rows = self._load()

        job_id = str(
            self._value(
                job,
                "job_id",
                "",
            )
            or ""
        )

        if not job_id:
            return False

        for row in rows:
            if str(row.get("job_id")) == job_id and row.get("status") == "PENDING":
                return False

        now = datetime.now(
            timezone.utc,
        ).isoformat()

        rows.append(
            {
                "job_id": job_id,
                "title": str(
                    self._value(
                        job,
                        "title",
                        "",
                    )
                    or ""
                ),
                "company": str(
                    self._value(
                        job,
                        "company",
                        "",
                    )
                    or ""
                ),
                "url": str(
                    self._value(
                        job,
                        "url",
                        "",
                    )
                    or self._value(
                        job,
                        "job_url",
                        "",
                    )
                    or ""
                ),
                "score": int(score or 0),
                "reason": reason,
                "source": "external_apply",
                "status": "PENDING",
                "run_id": run_id,
                "created_at": now,
                "updated_at": now,
            }
        )

        self._save(rows)

        return True
