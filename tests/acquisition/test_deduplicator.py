"""Tests for CrossProviderDeduplicator: merge and dedup logic."""
from __future__ import annotations

import pytest
from src.acquisition.models import JobProvenance, NormalizedJob
from src.acquisition.deduplicator import CrossProviderDeduplicator, _fingerprint, _jaccard


def _job(
    job_id: str,
    company: str = "Acme",
    title: str = "Engineer",
    location: str = "Pune",
    provider: str = "naukri",
    application_url: str = "",
    description: str = "",
    skills: list | None = None,
) -> NormalizedJob:
    return NormalizedJob(
        provider=provider,
        provider_job_id=job_id,
        provider_name=provider.capitalize(),
        provider_url=f"https://{provider}.com/{job_id}",
        application_url=application_url or f"https://{provider}.com/{job_id}",
        job_board=provider,
        company=company,
        title=title,
        description=description,
        skills=skills or [],
        location=location,
        provenance=JobProvenance(provider=provider, generated_query="q", search_profile="p"),
    )


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def test_jaccard_identical():
    assert _jaccard("python fastapi backend", "python fastapi backend") == 1.0

def test_jaccard_no_overlap():
    assert _jaccard("python backend", "java spring") == 0.0

def test_jaccard_partial():
    sim = _jaccard("python fastapi backend engineer", "backend engineer golang")
    assert 0.0 < sim < 1.0

def test_fingerprint_normalizes():
    j = _job("1", company="  Acme Corp. ", title="Sr. Engineer!!", location="Pune, MH")
    fp = _fingerprint(j)
    assert "acme corp" in fp
    assert "sr  engineer" in fp or "sr engineer" in fp


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def test_no_duplicates_unique():
    dedup = CrossProviderDeduplicator()
    jobs = [
        _job("1", company="AcmeCorp", title="SWE Backend", location="Mumbai", application_url="http://a.com/1"),
        _job("2", company="BetaInc", title="Platform Eng", location="Bangalore", application_url="http://a.com/2"),
    ]
    result, removed = dedup.deduplicate(jobs)
    assert len(result) == 2
    assert removed == 0


def test_exact_url_dedup():
    dedup = CrossProviderDeduplicator()
    url = "https://apply.company.com/jobs/123"
    j1 = _job("1", provider="naukri", application_url=url, skills=["Python"])
    j2 = _job("1", provider="google_jobs", application_url=url, skills=["FastAPI"])
    result, removed = dedup.deduplicate([j1, j2])
    assert len(result) == 1
    assert removed == 1


def test_fingerprint_dedup():
    dedup = CrossProviderDeduplicator()
    j1 = _job("id1", company="Acme", title="Backend Engineer", location="Pune", provider="naukri")
    j2 = _job("id2", company="Acme", title="Backend Engineer", location="Pune", provider="google_jobs")
    result, removed = dedup.deduplicate([j1, j2])
    assert len(result) == 1
    assert removed == 1


def test_description_jaccard_dedup():
    dedup = CrossProviderDeduplicator(jaccard_threshold=0.7)
    desc = "We are looking for a Python backend engineer to build REST APIs with FastAPI"
    j1 = _job("id1", company="TechCo", description=desc + " and deploy on AWS", provider="naukri")
    j2 = _job("id2", company="TechCo", description=desc + " and deploy on GCP", provider="remoteok")
    result, removed = dedup.deduplicate([j1, j2])
    assert len(result) == 1
    assert removed == 1


def test_metadata_merge_on_dedup():
    """Duplicate's skills and metadata are merged into winner."""
    dedup = CrossProviderDeduplicator()
    url = "https://apply.co/123"
    j1 = _job("1", provider="naukri", application_url=url, skills=["Python"])
    j2 = _job("1", provider="google_jobs", application_url=url, skills=["FastAPI"])
    result, _ = dedup.deduplicate([j1, j2])
    merged = result[0]
    assert "Python" in merged.skills
    assert "FastAPI" in merged.skills


def test_also_seen_on_populated():
    """Winner's provenance.also_seen_on tracks all duplicate providers."""
    dedup = CrossProviderDeduplicator()
    url = "https://apply.co/999"
    j1 = _job("x", provider="naukri", application_url=url)
    j2 = _job("x", provider="remoteok", application_url=url)
    result, _ = dedup.deduplicate([j1, j2])
    assert "remoteok" in result[0].provenance.also_seen_on


def test_empty_input():
    dedup = CrossProviderDeduplicator()
    result, removed = dedup.deduplicate([])
    assert result == []
    assert removed == 0
