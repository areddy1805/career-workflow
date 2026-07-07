import json
from types import SimpleNamespace

from src.application.manual_action_queue import (
    ManualActionQueue,
)


def test_external_job_is_added_to_queue(
    tmp_path,
):
    path = tmp_path / "manual_action_queue.json"

    queue = ManualActionQueue(path)

    candidate = SimpleNamespace(
        job_id="123",
        title="AI Engineer",
        company="Example Corp",
        url="https://example.com/job/123",
    )

    created = queue.enqueue_external_apply(
        job=candidate,
        score=90,
        reason="Strong GenAI fit",
        run_id="run-1",
    )

    assert created is True

    rows = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    assert len(rows) == 1
    assert rows[0]["job_id"] == "123"
    assert rows[0]["status"] == "PENDING"
    assert rows[0]["score"] == 90


def test_pending_job_is_not_duplicated(
    tmp_path,
):
    path = tmp_path / "manual_action_queue.json"

    queue = ManualActionQueue(path)

    candidate = SimpleNamespace(
        job_id="123",
        title="AI Engineer",
        company="Example Corp",
        url="https://example.com/job/123",
    )

    first = queue.enqueue_external_apply(
        job=candidate,
        score=90,
    )

    second = queue.enqueue_external_apply(
        job=candidate,
        score=90,
    )

    assert first is True
    assert second is False

    rows = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    assert len(rows) == 1
