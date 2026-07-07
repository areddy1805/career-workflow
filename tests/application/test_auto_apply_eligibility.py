from types import SimpleNamespace

from src.application.eligibility import (
    annotate_auto_apply_eligibility,
    evaluate_auto_apply_eligibility,
)


def job(
    job_id: str,
    title: str = "AI Engineer",
    company: str = "Example",
):
    return SimpleNamespace(
        job_id=job_id,
        title=title,
        company=company,
    )


def test_rejects_below_minimum_score():
    candidate = job("1")

    score_map = {
        "1": {
            "score": 67,
            "ai_reason": ("Genuine AI engineering role."),
        }
    }

    decision = evaluate_auto_apply_eligibility(
        candidate,
        score_map=score_map,
        minimum_score=68,
    )

    assert decision["eligible"] is False
    assert "below_minimum_score" in decision["reasons"]


def test_stack_mismatch_is_not_hard_rejection():
    candidate = job(
        "1",
        title="Machine Learning Engineer",
    )

    score_map = {
        "1": {
            "score": 72,
            "ai_reason": (
                "Genuine AI role with substantial "
                "stack mismatch. Requires TensorFlow, "
                "C++, and traditional ML model training."
            ),
        }
    }

    decision = evaluate_auto_apply_eligibility(
        candidate,
        score_map=score_map,
        minimum_score=68,
    )

    assert decision["eligible"] is True
    assert decision["reasons"] == []


def test_cloud_mismatch_is_not_hard_rejection():
    candidate = job(
        "1",
        title="AI Engineer",
    )

    score_map = {
        "1": {
            "score": 75,
            "ai_reason": (
                "Genuine AI role. Significant stack "
                "mismatch because role requires GCP "
                "while candidate primarily uses Azure."
            ),
        }
    }

    decision = evaluate_auto_apply_eligibility(
        candidate,
        score_map=score_map,
        minimum_score=68,
    )

    assert decision["eligible"] is True


def test_incidental_ai_is_rejected():
    candidate = job(
        "1",
        title="Full Stack Developer",
    )

    score_map = {
        "1": {
            "score": 75,
            "ai_reason": (
                "Generic full stack role with only "
                "incidental AI. AI is listed as a "
                "minor responsibility."
            ),
        }
    }

    decision = evaluate_auto_apply_eligibility(
        candidate,
        score_map=score_map,
        minimum_score=68,
    )

    assert decision["eligible"] is False
    assert "incidental_ai" in decision["reasons"]


def test_non_engineering_ai_is_rejected():
    candidate = job(
        "1",
        title="AI Copywriter",
    )

    score_map = {
        "1": {
            "score": 80,
            "ai_reason": (
                "AI copywriter role focused on " "brand copy and content creation."
            ),
        }
    }

    decision = evaluate_auto_apply_eligibility(
        candidate,
        score_map=score_map,
        minimum_score=68,
    )

    assert decision["eligible"] is False
    assert "non_engineering_ai" in decision["reasons"]


def test_fresher_role_is_rejected():
    candidate = job(
        "1",
        title="Junior AI Developer",
    )

    score_map = {
        "1": {
            "score": 85,
            "ai_reason": (
                "Strong AI role but targets a fresher " "with 0-2 years of experience."
            ),
        }
    }

    decision = evaluate_auto_apply_eligibility(
        candidate,
        score_map=score_map,
        minimum_score=68,
    )

    assert decision["eligible"] is False
    assert "severe_seniority_mismatch" in decision["reasons"]


def test_annotation_returns_all_decisions():
    jobs = [
        job("1"),
        job("2"),
        job("3"),
    ]

    score_map = {
        "1": {
            "score": 90,
            "ai_reason": "Direct GenAI role.",
        },
        "2": {
            "score": 62,
            "ai_reason": "Genuine ML role.",
        },
        "3": {
            "score": 80,
            "ai_reason": ("Generic software role with " "incidental AI."),
        },
    }

    eligible, decisions = annotate_auto_apply_eligibility(
        jobs,
        score_map=score_map,
        minimum_score=68,
    )

    assert [candidate.job_id for candidate in eligible] == ["1"]

    assert len(decisions) == 3

    rejected = [decision for decision in decisions if not decision["eligible"]]

    assert len(rejected) == 2
