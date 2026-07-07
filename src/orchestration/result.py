from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PipelineResult:
    run_id: str
    status: str

    acquired: int = 0
    classified: int = 0
    selected: int = 0

    attempted: int = 0
    submitted: int = 0
    failed: int = 0
    manual_review: int = 0

    started_at: datetime | None = None
    completed_at: datetime | None = None

    stage_results: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)

        if self.started_at is not None:
            data["started_at"] = self.started_at.isoformat()

        if self.completed_at is not None:
            data["completed_at"] = self.completed_at.isoformat()

        return data
