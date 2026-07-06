from dataclasses import dataclass
from typing import Any

import apply_agent
from apply_agent import run_application_batch
from src.application.outcome import (
    ApplicationOutcome,
    ApplicationStatus,
)


@dataclass
class FakeJob:
    job_id: str
    title: str = "AI Engineer"
    company: str = "Example Company"
    tags: list[str] | None = None

    def __post_init__(self) -> None:
        if self.tags is None:
            self.tags = [
                "Python",
                "RAG",
                "FastAPI",
            ]


class FakeResolver:
    def resolve(
        self,
        question: dict,
        profile: dict,
    ) -> Any:
        raise AssertionError(
            "Resolver should not be called in batch orchestration tests."
        )


class FakeBatchClient:
    def __init__(
        self,
        external_job_ids: set[str] | None = None,
    ):
        self.external_job_ids = external_job_ids or set()
        self.external_checks: list[str] = []

    def is_external_apply(
        self,
        job_id: str,
    ) -> bool:
        self.external_checks.append(job_id)

        return job_id in self.external_job_ids


def make_outcome(
    job_id: str,
    status: ApplicationStatus,
) -> ApplicationOutcome:
    return ApplicationOutcome(
        status=status,
        job_id=job_id,
        response={},
        reasoning=f"Test outcome: {status.value}",
    )


def test_local_applied_job_is_skipped_without_network_call(
    monkeypatch,
) -> None:
    job = FakeJob(job_id="1")

    client = FakeBatchClient()

    process_calls: list[str] = []
    saved_jobs: list[str] = []
    sleep_calls: list[int] = []

    def fake_process(**kwargs):
        process_calls.append(kwargs["job"].job_id)

        return make_outcome(
            job_id="1",
            status=ApplicationStatus.APPLIED,
        )

    monkeypatch.setattr(
        apply_agent,
        "process_job_application",
        fake_process,
    )

    summary = run_application_batch(
        jc=client,
        jobs=[job],
        score_map={"1": {}},
        questionnaire_resolver=FakeResolver(),
        applied_jobs_set={"1"},
        sleep_fn=sleep_calls.append,
        save_fn=lambda item: saved_jobs.append(item.job_id),
    )

    assert summary.total_candidates == 1
    assert summary.skipped_local == 1
    assert summary.applied == 0
    assert summary.failed == 0

    assert client.external_checks == []
    assert process_calls == []
    assert saved_jobs == []
    assert sleep_calls == []


def test_external_job_is_skipped() -> None:
    job = FakeJob(job_id="1")

    client = FakeBatchClient(
        external_job_ids={"1"},
    )

    saved_jobs: list[str] = []
    sleep_calls: list[int] = []

    summary = run_application_batch(
        jc=client,
        jobs=[job],
        score_map={"1": {}},
        questionnaire_resolver=FakeResolver(),
        applied_jobs_set=set(),
        sleep_fn=sleep_calls.append,
        save_fn=lambda item: saved_jobs.append(item.job_id),
    )

    assert summary.skipped_external == 1
    assert summary.applied == 0
    assert summary.failed == 0

    assert client.external_checks == ["1"]
    assert saved_jobs == []
    assert sleep_calls == []


def test_successful_application_is_persisted(
    monkeypatch,
) -> None:
    job = FakeJob(job_id="1")

    client = FakeBatchClient()

    applied_jobs_set: set[str] = set()
    saved_jobs: list[str] = []
    sleep_calls: list[int] = []

    monkeypatch.setattr(
        apply_agent,
        "process_job_application",
        lambda **kwargs: make_outcome(
            job_id=kwargs["job"].job_id,
            status=ApplicationStatus.APPLIED,
        ),
    )

    summary = run_application_batch(
        jc=client,
        jobs=[job],
        score_map={"1": {}},
        questionnaire_resolver=FakeResolver(),
        applied_jobs_set=applied_jobs_set,
        sleep_fn=sleep_calls.append,
        save_fn=lambda item: saved_jobs.append(item.job_id),
    )

    assert summary.applied == 1
    assert summary.failed == 0

    assert applied_jobs_set == {"1"}
    assert saved_jobs == ["1"]
    assert sleep_calls == [3]


def test_server_already_applied_repairs_local_state(
    monkeypatch,
) -> None:
    job = FakeJob(job_id="1")

    client = FakeBatchClient()

    applied_jobs_set: set[str] = set()
    saved_jobs: list[str] = []
    sleep_calls: list[int] = []

    monkeypatch.setattr(
        apply_agent,
        "process_job_application",
        lambda **kwargs: make_outcome(
            job_id=kwargs["job"].job_id,
            status=ApplicationStatus.ALREADY_APPLIED,
        ),
    )

    summary = run_application_batch(
        jc=client,
        jobs=[job],
        score_map={"1": {}},
        questionnaire_resolver=FakeResolver(),
        applied_jobs_set=applied_jobs_set,
        sleep_fn=sleep_calls.append,
        save_fn=lambda item: saved_jobs.append(item.job_id),
    )

    assert summary.already_applied == 1
    assert summary.applied == 0
    assert summary.failed == 0

    assert applied_jobs_set == {"1"}
    assert saved_jobs == ["1"]
    assert sleep_calls == [3]


def test_failed_job_does_not_stop_batch(
    monkeypatch,
) -> None:
    jobs = [
        FakeJob(job_id="1"),
        FakeJob(job_id="2"),
    ]

    client = FakeBatchClient()

    process_calls: list[str] = []
    saved_jobs: list[str] = []
    sleep_calls: list[int] = []

    def fake_process(**kwargs):
        job_id = kwargs["job"].job_id

        process_calls.append(job_id)

        if job_id == "1":
            raise RuntimeError("Simulated failure")

        return make_outcome(
            job_id=job_id,
            status=ApplicationStatus.APPLIED,
        )

    monkeypatch.setattr(
        apply_agent,
        "process_job_application",
        fake_process,
    )

    summary = run_application_batch(
        jc=client,
        jobs=jobs,
        score_map={
            "1": {},
            "2": {},
        },
        questionnaire_resolver=FakeResolver(),
        applied_jobs_set=set(),
        sleep_fn=sleep_calls.append,
        save_fn=lambda item: saved_jobs.append(item.job_id),
    )

    assert process_calls == [
        "1",
        "2",
    ]

    assert summary.total_candidates == 2
    assert summary.applied == 1
    assert summary.failed == 1

    assert saved_jobs == ["2"]

    assert sleep_calls == [
        3,
        3,
    ]


def test_non_success_outcome_counts_as_failure(
    monkeypatch,
) -> None:
    job = FakeJob(job_id="1")

    client = FakeBatchClient()

    saved_jobs: list[str] = []
    sleep_calls: list[int] = []

    monkeypatch.setattr(
        apply_agent,
        "process_job_application",
        lambda **kwargs: make_outcome(
            job_id=kwargs["job"].job_id,
            status=ApplicationStatus.UNKNOWN,
        ),
    )

    summary = run_application_batch(
        jc=client,
        jobs=[job],
        score_map={"1": {}},
        questionnaire_resolver=FakeResolver(),
        applied_jobs_set=set(),
        sleep_fn=sleep_calls.append,
        save_fn=lambda item: saved_jobs.append(item.job_id),
    )

    assert summary.applied == 0
    assert summary.failed == 1

    assert saved_jobs == []
    assert sleep_calls == [3]
