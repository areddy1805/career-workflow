from __future__ import annotations

import os
import re
from collections import Counter
from typing import Any

INCIDENTAL_AI_PATTERNS = (
    r"\bincidental ai\b",
    r"\bincidental automation\b",
    r"\bai aspect (?:is|appears) merely incidental\b",
    r"\bgeneric .* role with only incidental ai\b",
    r"\bdoes not require production ai engineering\b",
    r"\bai is listed as a minor responsibility\b",
    r"\bai terminology rather than\b",
)


NON_ENGINEERING_AI_PATTERNS = (
    r"\bcopywriter\b",
    r"\bbrand copy\b",
    r"\bmarketing\b",
    r"\bsales\b",
    r"\bcontent writer\b",
    r"\bcontent creation\b",
    r"\bnon-engineering ai\b",
)


SEVERE_SENIORITY_MISMATCH_PATTERNS = (
    r"\bfresher\b",
    r"\b0\s*[-–]\s*1 years?\b",
    r"\b0\s*[-–]\s*2 years?\b",
    r"\b1\s*[-–]\s*2 years?\b",
    r"\bjunior role\b",
    r"\btargets? (?:a )?fresher\b",
    r"\btargets? 1\s*[-–]\s*2 years?\b",
    r"\bsevere seniority mismatch\b",
    r"\bsignificant seniority mismatch\b",
)


def _normalize_text(value: Any) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(value or "").strip().lower(),
    )


def _matches_any(
    text: str,
    patterns: tuple[str, ...],
) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _job_id(job: Any) -> str:
    if isinstance(job, dict):
        return str(job.get("job_id") or "")

    return str(getattr(job, "job_id", "") or "")


def _job_title(job: Any) -> str:
    if isinstance(job, dict):
        return str(job.get("title") or "")

    return str(getattr(job, "title", "") or "")


def _job_company(job: Any) -> str:
    if isinstance(job, dict):
        return str(job.get("company") or "")

    return str(getattr(job, "company", "") or "")


def _score_for_job(
    job: Any,
    score_map: dict[str, dict],
) -> int:
    job_id = _job_id(job)

    result = score_map.get(job_id, {})

    try:
        return int(
            result.get(
                "score",
                result.get("ai_score", 0),
            )
            or 0
        )
    except (TypeError, ValueError):
        return 0


def _reason_text_for_job(
    job: Any,
    score_map: dict[str, dict],
) -> str:
    result = score_map.get(
        _job_id(job),
        {},
    )

    values = (
        result.get("ai_reason"),
        result.get("ai_detail"),
        result.get("reason"),
        result.get("title"),
        _job_title(job),
    )

    return _normalize_text(" ".join(str(value) for value in values if value))


def evaluate_auto_apply_eligibility(
    job: Any,
    *,
    score_map: dict[str, dict],
    minimum_score: int | None = None,
) -> dict:
    if minimum_score is None:
        minimum_score = int(
            os.getenv(
                "AUTO_APPLY_MIN_SCORE",
                os.getenv(
                    "AUTO_APPLY_MIN_SCORE",
                    "68",
                ),
            )
        )

    score = _score_for_job(
        job,
        score_map,
    )

    reason_text = _reason_text_for_job(
        job,
        score_map,
    )

    reasons: list[str] = []

    if score < minimum_score:
        reasons.append("below_minimum_score")

    if _matches_any(
        reason_text,
        INCIDENTAL_AI_PATTERNS,
    ):
        reasons.append("incidental_ai")

    if _matches_any(
        reason_text,
        NON_ENGINEERING_AI_PATTERNS,
    ):
        reasons.append("non_engineering_ai")

    if _matches_any(
        reason_text,
        SEVERE_SENIORITY_MISMATCH_PATTERNS,
    ):
        reasons.append("severe_seniority_mismatch")

    # Deliberately NOT hard-rejected:
    #
    # - TensorFlow mismatch
    # - PyTorch mismatch
    # - C# mismatch
    # - Java mismatch
    # - C++ mismatch
    # - traditional ML focus
    # - data science focus
    # - MLOps focus
    # - computer vision focus
    # - cloud-provider mismatch
    # - framework mismatch
    #
    # These factors belong in scoring/ranking, not hard eligibility.

    return {
        "job_id": _job_id(job),
        "title": _job_title(job),
        "company": _job_company(job),
        "score": score,
        "minimum_score": minimum_score,
        "eligible": not reasons,
        "reasons": reasons,
        "primary_reason": (reasons[0] if reasons else None),
    }


def annotate_auto_apply_eligibility(
    jobs: list[Any],
    *,
    score_map: dict[str, dict],
    minimum_score: int | None = None,
) -> tuple[list[Any], list[dict]]:
    eligible_jobs: list[Any] = []

    decisions: list[dict] = []

    for job in jobs:
        decision = evaluate_auto_apply_eligibility(
            job,
            score_map=score_map,
            minimum_score=minimum_score,
        )

        decisions.append(decision)

        if decision["eligible"]:
            eligible_jobs.append(job)

    return eligible_jobs, decisions


def eligibility_rejection_summary(
    decisions: list[dict],
) -> dict[str, int]:
    counter: Counter[str] = Counter()

    for decision in decisions:
        if decision.get("eligible"):
            continue

        reasons = decision.get("reasons") or ["unknown_rejection_reason"]

        for reason in reasons:
            counter[str(reason)] += 1

    return dict(
        sorted(
            counter.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )
    )
