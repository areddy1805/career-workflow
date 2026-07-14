"""Tests for JobNormalizer: NormalizedJob → Job conversion."""
from __future__ import annotations

import pytest
from src.acquisition.models import (
    JobProvenance, NormalizedJob, ProviderType,
)
from src.acquisition.normalizer import JobNormalizer


def _make_normalized(
    provider="naukri", supports_auto_apply=True, **kwargs
) -> NormalizedJob:
    defaults = dict(
        provider=provider,
        provider_job_id="42",
        provider_name="Naukri",
        provider_url="https://naukri.com/job-listings-42",
        application_url="https://naukri.com/apply/42",
        job_board="naukri",
        company="Acme Corp",
        title="Software Engineer",
        description="Build great things",
        skills=["Python", "FastAPI"],
        technologies=["Python"],
        salary="20-30 LPA",
        experience="3-5 years",
        location="Pune, Maharashtra",
        employment_type="full_time",
        remote_type="hybrid",
        posted_date="2024-01-15",
        provenance=JobProvenance(
            provider=provider,
            generated_query="software engineer python",
            search_profile="applied_ai",
            technology_group="python_ai",
            track="TIER_A",
            matched_technology="python",
        ),
    )
    defaults.update(kwargs)
    return NormalizedJob(**defaults)


def test_normalized_to_job_basic():
    nj = _make_normalized()
    job = JobNormalizer.normalized_to_job(nj, supports_auto_apply=True)
    assert job.job_id == "42"
    assert job.title == "Software Engineer"
    assert job.company == "Acme Corp"
    assert job.location == "Pune, Maharashtra"
    assert job.salary == "20-30 LPA"
    assert "Python" in job.tags


def test_is_external_apply_false_for_auto_apply():
    nj = _make_normalized(provider="naukri")
    job = JobNormalizer.normalized_to_job(nj, supports_auto_apply=True)
    assert job.is_external_apply is False


def test_is_external_apply_true_for_non_auto_apply():
    nj = _make_normalized(provider="remoteok", provider_name="RemoteOK")
    job = JobNormalizer.normalized_to_job(nj, supports_auto_apply=False)
    assert job.is_external_apply is True


def test_provenance_attributes_preserved():
    nj = _make_normalized()
    job = JobNormalizer.normalized_to_job(nj, supports_auto_apply=True)
    assert job.search_profile == "applied_ai"
    assert job.search_query == "software engineer python"
    assert job.matched_technology == "python"
    assert job.search_track == "TIER_A"
    assert job.technology_group == "python_ai"


def test_provider_attributes_set():
    nj = _make_normalized(provider="google_jobs", provider_name="Google Jobs")
    job = JobNormalizer.normalized_to_job(nj, supports_auto_apply=False)
    assert job.provider == "google_jobs"
    assert job.provider_name == "Google Jobs"
    assert job.application_url == nj.application_url
    assert job.original_job_url == nj.provider_url
    assert job.apply_source == "Google Jobs"


def test_batch_conversion():
    jobs_nj = [_make_normalized(provider_job_id=str(i)) for i in range(5)]
    caps_map = {"naukri": True}
    jobs = JobNormalizer.batch(jobs_nj, caps_map)
    assert len(jobs) == 5
    for j in jobs:
        assert j.is_external_apply is False  # naukri


def test_batch_skips_failed_conversions(monkeypatch):
    """batch() skips jobs that fail normalization and returns the rest."""
    def bad_normalize(nj, **kwargs):
        if nj.provider_job_id == "bad":
            raise ValueError("intentional")
        from src.models.models import Job
        j = Job(job_id=nj.provider_job_id, title=nj.title, company=nj.company,
                location=nj.location, experience=nj.experience, salary=nj.salary,
                posted_date=nj.posted_date, apply_link=nj.application_url,
                description=nj.description, tags=nj.skills)
        return j

    monkeypatch.setattr(JobNormalizer, "normalized_to_job", staticmethod(bad_normalize))
    jobs_nj = [_make_normalized(provider_job_id="bad"), _make_normalized(provider_job_id="good")]
    result = JobNormalizer.batch(jobs_nj, {})
    assert len(result) == 1
    assert result[0].job_id == "good"
