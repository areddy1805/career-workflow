"""Tests for AcquisitionManager: orchestration, failure isolation, stats."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from src.acquisition.models import (
    NormalizedJob, JobProvenance, SearchPlan,
    ProviderCapabilities, ProviderHealthStatus, ProviderHealth, ProviderType,
)
from src.acquisition.manager import AcquisitionManager
from src.acquisition.deduplicator import CrossProviderDeduplicator
from src.acquisition.provider import JobProvider


def _nj(job_id: str, provider: str = "test", company: str | None = None) -> NormalizedJob:
    return NormalizedJob(
        provider=provider, provider_job_id=job_id, provider_name=provider,
        provider_url=f"https://{provider}/{job_id}",
        application_url=f"https://{provider}/{job_id}/{job_id}",  # unique URL
        job_board=provider, company=company or f"Company_{provider}_{job_id}", title=f"SWE_{job_id}",
        location=f"City_{job_id}",
        provenance=JobProvenance(provider=provider, generated_query="q", search_profile="p"),
    )


def _plan(query: str = "python", provider: str | None = None) -> SearchPlan:
    return SearchPlan(
        profile="test_profile",
        generated_query=query,
        location="Pune",
        target_providers=[provider] if provider else [],
        priority=50,
    )


def _mock_provider(name: str, jobs: list, fail: bool = False) -> MagicMock:
    p = MagicMock(spec=JobProvider)
    p.PROVIDER_NAME = name
    p.PROVIDER_TYPE = ProviderType.JOB_BOARD
    p._config = {}
    p._cfg = lambda k, d=None: d
    p.capabilities.return_value = ProviderCapabilities(supports_auto_apply=False)
    if fail:
        p.search.side_effect = RuntimeError("Provider failed")
    else:
        p.search.return_value = jobs
    return p


def _mock_registry(providers: list) -> MagicMock:
    reg = MagicMock()
    reg.enabled_providers.return_value = providers
    reg.capabilities_map.return_value = {p.PROVIDER_NAME: p.capabilities() for p in providers}
    reg.supports_auto_apply_map.return_value = {p.PROVIDER_NAME: False for p in providers}
    reg.get_provider.return_value = None
    reg.shutdown_all.return_value = None
    return reg


# ---------------------------------------------------------------------------

def test_acquire_happy_path():
    jobs_a = [_nj("1", "provider_a"), _nj("2", "provider_a")]
    jobs_b = [_nj("3", "provider_b")]
    pa = _mock_provider("provider_a", jobs_a)
    pb = _mock_provider("provider_b", jobs_b)
    registry = _mock_registry([pa, pb])

    manager = AcquisitionManager(registry=registry)
    with patch("src.acquisition.normalizer.JobNormalizer.batch", side_effect=lambda jobs, caps: jobs):
        result, summary = manager.acquire([_plan()])

    assert summary.total_jobs_returned == 3
    assert summary.total_unique_jobs == 3
    assert len(summary.provider_stats) == 2


def test_one_provider_fails_others_succeed():
    jobs_b = [_nj("1", "provider_b")]
    pa = _mock_provider("provider_a", [], fail=True)
    pb = _mock_provider("provider_b", jobs_b)
    registry = _mock_registry([pa, pb])

    manager = AcquisitionManager(registry=registry)
    with patch("src.acquisition.normalizer.JobNormalizer.batch", side_effect=lambda jobs, caps: jobs):
        result, summary = manager.acquire([_plan()])

    stats_a = next(s for s in summary.provider_stats if s.provider == "provider_a")
    stats_b = next(s for s in summary.provider_stats if s.provider == "provider_b")
    assert stats_a.failures == 1
    assert stats_b.unique_jobs == 1


def test_cross_provider_dedup_counted():
    url = "https://apply.co/same"
    j1 = _nj("1", "naukri"); j1.application_url = url
    j2 = _nj("1", "google_jobs"); j2.application_url = url
    pa = _mock_provider("naukri", [j1])
    pb = _mock_provider("google_jobs", [j2])
    registry = _mock_registry([pa, pb])

    manager = AcquisitionManager(registry=registry, deduplicator=CrossProviderDeduplicator())
    with patch("src.acquisition.normalizer.JobNormalizer.batch", side_effect=lambda jobs, caps: jobs):
        result, summary = manager.acquire([_plan()])

    assert summary.cross_provider_duplicates == 1
    assert summary.total_unique_jobs == 1


def test_empty_providers_returns_empty():
    registry = _mock_registry([])
    manager = AcquisitionManager(registry=registry)
    result, summary = manager.acquire([_plan()])
    assert result == []
    assert summary.total_unique_jobs == 0


def test_provider_filter_applies():
    """Plans with target_providers filter which providers run the plan."""
    pa = _mock_provider("naukri", [_nj("1")])
    pb = _mock_provider("google_jobs", [_nj("2")])
    registry = _mock_registry([pa, pb])

    plan = _plan("python", provider="naukri")
    manager = AcquisitionManager(registry=registry)
    with patch("src.acquisition.normalizer.JobNormalizer.batch", side_effect=lambda jobs, caps: jobs):
        manager.acquire([plan])

    # Only naukri should have been called for this plan
    pa.search.assert_called_once()
    pb.search.assert_not_called()


def test_acquisition_summary_pcts():
    pa = _mock_provider("p_a", [_nj("1"), _nj("2")])
    pb = _mock_provider("p_b", [_nj("3")])
    registry = _mock_registry([pa, pb])

    manager = AcquisitionManager(registry=registry)
    with patch("src.acquisition.normalizer.JobNormalizer.batch", side_effect=lambda jobs, caps: jobs):
        _, summary = manager.acquire([_plan()])

    assert summary.coverage_pct == 100.0
    d = summary.to_dict()
    assert "coverage_pct" in d
    assert "provider_contribution_pct" in d
