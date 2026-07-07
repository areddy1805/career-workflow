from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from src.application.analytics import (
    breakdown,
    has_response,
)


@dataclass(
    frozen=True,
)
class AdaptiveStrategyConfig:
    enabled: bool = True

    minimum_applications: int = 30

    minimum_responses: int = 5

    base_minimum_score: int = 68

    base_max_applications_per_run: int = 5

    minimum_group_samples: int = 5

    exploration_fraction: float = 0.20


@dataclass(
    frozen=True,
)
class AdaptiveStrategy:
    active: bool

    reason: str

    minimum_score: int

    max_applications_per_run: int

    preferred_priorities: tuple[str, ...]

    preferred_subtracks: tuple[str, ...]

    exploration_fraction: float

    total_applications: int

    total_responses: int


def _rank_dimension(
    rows: list[dict[str, Any]],
    *,
    dimension: str,
    minimum_samples: int,
) -> tuple[str, ...]:
    report = breakdown(
        rows,
        dimension=dimension,
    )

    eligible = [
        row
        for row in report
        if (
            int(row["total"]) >= minimum_samples
            and str(row["dimension_value"]) != "UNCLASSIFIED"
        )
    ]

    ranked = sorted(
        eligible,
        key=lambda row: (
            -float(row["interview_rate"]),
            -float(row["response_rate"]),
            -int(row["total"]),
            str(row["dimension_value"]),
        ),
    )

    return tuple(str(row["dimension_value"]) for row in ranked)


def build_adaptive_strategy(
    rows: Iterable[dict[str, Any]],
    *,
    config: AdaptiveStrategyConfig | None = None,
) -> AdaptiveStrategy:
    effective = config or AdaptiveStrategyConfig()

    population = list(
        rows,
    )

    total = len(
        population,
    )

    responses = sum(1 for row in population if has_response(row))

    inactive = (
        not effective.enabled
        or total < effective.minimum_applications
        or responses < effective.minimum_responses
    )

    if inactive:
        if not effective.enabled:
            reason = "disabled"

        elif total < effective.minimum_applications:
            reason = "insufficient_application_sample"

        else:
            reason = "insufficient_response_sample"

        return AdaptiveStrategy(
            active=False,
            reason=reason,
            minimum_score=(effective.base_minimum_score),
            max_applications_per_run=(effective.base_max_applications_per_run),
            preferred_priorities=(),
            preferred_subtracks=(),
            exploration_fraction=(effective.exploration_fraction),
            total_applications=total,
            total_responses=responses,
        )

    priorities = _rank_dimension(
        population,
        dimension="priority",
        minimum_samples=(effective.minimum_group_samples),
    )

    subtracks = _rank_dimension(
        population,
        dimension="subtrack",
        minimum_samples=(effective.minimum_group_samples),
    )

    response_rate = responses / total if total else 0.0

    minimum_score = effective.base_minimum_score

    max_per_run = effective.base_max_applications_per_run

    if response_rate < 0.05:
        minimum_score = max(
            minimum_score,
            75,
        )

        max_per_run = min(
            max_per_run,
            4,
        )

    elif response_rate >= 0.15:
        max_per_run = max(
            max_per_run,
            6,
        )

    return AdaptiveStrategy(
        active=True,
        reason="sufficient_outcome_evidence",
        minimum_score=minimum_score,
        max_applications_per_run=max_per_run,
        preferred_priorities=priorities,
        preferred_subtracks=subtracks,
        exploration_fraction=(effective.exploration_fraction),
        total_applications=total,
        total_responses=responses,
    )


def _preference_rank(
    value: str,
    preferences: tuple[str, ...],
) -> int:
    try:
        return preferences.index(value)

    except ValueError:
        return len(preferences) + 1


def rank_candidates_adaptively(
    jobs: list[Any],
    *,
    score_map: dict[str, dict[str, Any]],
    strategy: AdaptiveStrategy,
) -> list[Any]:
    """
    Re-rank candidates without excluding exploration candidates.

    Safety:
    adaptive strategy changes ordering only.
    Existing policy remains responsible for hard eligibility decisions.
    """

    if not strategy.active:
        return list(
            jobs,
        )

    def ranking_key(
        job: Any,
    ) -> tuple:
        meta = score_map.get(
            str(job.job_id),
            {},
        )

        priority = str(meta.get("priority") or "")

        subtrack = str(meta.get("subtrack") or "")

        score = int(meta.get("score") or 0)

        score_eligible = score >= strategy.minimum_score

        return (
            0 if score_eligible else 1,
            _preference_rank(
                priority,
                strategy.preferred_priorities,
            ),
            _preference_rank(
                subtrack,
                strategy.preferred_subtracks,
            ),
            -score,
        )

    return sorted(
        jobs,
        key=ranking_key,
    )
