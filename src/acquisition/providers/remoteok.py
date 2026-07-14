"""
src/acquisition/providers/remoteok.py — RemoteOK provider.

Uses the public JSON API at https://remoteok.com/api (no auth required).
Returns remote-only jobs globally.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from src.acquisition.models import (
    JobProvenance,
    NormalizedJob,
    ProviderCapabilities,
    ProviderHealth,
    ProviderHealthStatus,
    ProviderType,
    SearchPlan,
)
from src.acquisition.provider import JobProvider

logger = logging.getLogger(__name__)

_API_URL = "https://remoteok.com/api"


class RemoteOKProvider(JobProvider):
    """
    RemoteOK job board provider.
    Queries the public JSON API with tag/keyword filtering.
    No authentication required.
    """

    PROVIDER_NAME = "remoteok"
    PROVIDER_TYPE = ProviderType.JOB_BOARD

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._initialized = True
        self._last_fetch: list[dict] = []
        self._last_fetch_time: float = 0.0

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_auto_apply=False,
            authentication_required=False,
            supports_login=False,
            supports_pagination=False,  # API returns all at once
            supports_location_filter=False,  # remote only
            supports_remote_filter=True,
            supports_salary_filter=False,
            supports_experience_filter=False,
            rate_limited=True,
            captcha_risk=False,
        )

    def health(self) -> ProviderHealth:
        if requests is None:
            return ProviderHealth(
                provider=self.PROVIDER_NAME,
                status=ProviderHealthStatus.UNAVAILABLE,
                error="requests library not installed",
            )
        return self._make_healthy()

    def search(self, plan: SearchPlan) -> list[NormalizedJob]:
        """Fetch jobs from RemoteOK matching the search plan keywords."""
        try:
            raw_jobs = self._fetch_api()
        except Exception as exc:
            logger.warning("RemoteOK fetch failed: %s", exc)
            return []

        query_terms = set(plan.generated_query.lower().split())
        matched = []

        for raw in raw_jobs:
            if not isinstance(raw, dict) or raw.get("slug") == "legal":
                continue
            if self._matches(raw, query_terms):
                try:
                    nj = self.normalize(raw)
                    nj.provenance.generated_query = plan.generated_query
                    nj.provenance.search_profile = plan.profile
                    nj.provenance.technology_group = plan.technology_group
                    nj.provenance.track = plan.track
                    nj.provenance.matched_technology = plan.matched_technology
                    matched.append(nj)
                except Exception as exc:
                    logger.debug("RemoteOK normalize error: %s", exc)

        max_r = self._max_results()
        return matched[:max_r]

    def normalize(self, raw: Any) -> NormalizedJob:
        job_id = str(raw.get("id", "") or raw.get("slug", ""))
        slug = raw.get("slug", job_id)
        url = f"https://remoteok.com/remote-jobs/{slug}"

        tags = [str(t) for t in (raw.get("tags") or []) if t]
        company = str(raw.get("company", "") or "")
        title = str(raw.get("position", "") or raw.get("title", "") or "")

        salary_min = raw.get("salary_min") or 0
        salary_max = raw.get("salary_max") or 0
        salary = ""
        if salary_min or salary_max:
            salary = f"${salary_min:,} - ${salary_max:,}" if salary_max else f"${salary_min:,}+"

        posted_epoch = raw.get("epoch", 0)
        posted_date = ""
        if posted_epoch:
            try:
                posted_date = datetime.fromtimestamp(posted_epoch, tz=timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                pass

        return NormalizedJob(
            provider=self.PROVIDER_NAME,
            provider_job_id=job_id,
            provider_name="RemoteOK",
            provider_url=url,
            application_url=raw.get("apply_url") or raw.get("url") or url,
            job_board="remoteok",
            company=company,
            title=title,
            description=str(raw.get("description", "") or ""),
            skills=tags,
            technologies=tags,
            salary=salary,
            experience="",
            location="Remote",
            employment_type="full_time",
            remote_type="remote",
            posted_date=posted_date,
            provenance=JobProvenance(
                provider=self.PROVIDER_NAME,
                generated_query="",
                search_profile="",
            ),
            provider_metadata={
                "tags": tags,
                "logo": raw.get("logo", ""),
                "company_url": raw.get("company_url", ""),
                "salary_min": salary_min,
                "salary_max": salary_max,
            },
        )

    def shutdown(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fetch_api(self) -> list[dict]:
        """Fetch all jobs from RemoteOK API. Cached for 60s to avoid hammering."""
        now = time.time()
        if self._last_fetch and (now - self._last_fetch_time) < 60:
            return self._last_fetch

        if requests is None:
            raise RuntimeError("requests library not available")

        headers = {
            "User-Agent": self._user_agent(),
            "Accept": "application/json",
        }
        resp = requests.get(
            _API_URL,
            headers=headers,
            timeout=(self._connect_timeout(), self._read_timeout()),
        )
        resp.raise_for_status()

        data = resp.json()
        # First element is always the legal notice dict
        self._last_fetch = [item for item in data if isinstance(item, dict)]
        self._last_fetch_time = now

        logger.debug("RemoteOK API returned %d jobs", len(self._last_fetch))
        return self._last_fetch

    def _matches(self, raw: dict, query_terms: set[str]) -> bool:
        """Check if a job matches the query terms."""
        if not query_terms:
            return True

        searchable = " ".join([
            str(raw.get("position", "") or ""),
            str(raw.get("company", "") or ""),
            " ".join(str(t) for t in (raw.get("tags") or [])),
            str(raw.get("description", "") or "")[:500],
        ]).lower()

        return any(term in searchable for term in query_terms)
