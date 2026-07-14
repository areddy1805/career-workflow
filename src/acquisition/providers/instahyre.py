"""
src/acquisition/providers/instahyre.py — Instahyre provider.
Curated job board focused on quality companies. No automatic application.
"""
from __future__ import annotations

import logging
from typing import Any

from src.acquisition.models import (
    JobProvenance, NormalizedJob, ProviderCapabilities,
    ProviderHealth, ProviderType, SearchPlan,
)
from src.acquisition.provider import JobProvider

logger = logging.getLogger(__name__)


class InstahyreProvider(JobProvider):
    PROVIDER_NAME = "instahyre"
    PROVIDER_TYPE = ProviderType.JOB_BOARD
    LIFECYCLE_STATE = "experimental"

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._initialized = True

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            native_apply=False,
            external_apply=True,
            manual_only=False,
            playwright_supported=False,
            authentication_required=False,
            supports_pagination=True,
            supports_location_filter=True,
            supports_experience_filter=True,
            rate_limited=True,
            captcha_risk=False,
        )

    def health(self) -> ProviderHealth:
        return self._make_healthy()

    def search(self, plan: SearchPlan) -> list[NormalizedJob]:
        try:
            import requests
        except ImportError:
            return []

        params = {
            "designation": plan.generated_query,
            "location": plan.location or "",
            "experience": plan.experience or "",
            "page": 1,
        }

        try:
            resp = requests.get(
                "https://www.instahyre.com/api/v1/opportunity/",
                params=params,
                headers={"User-Agent": self._user_agent()},
                timeout=(self._connect_timeout(), self._read_timeout()),
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("Instahyre search failed: %s", exc)
            return []

        results = data.get("results", data) if isinstance(data, dict) else data
        jobs = []
        for item in (results or [])[:self._max_results()]:
            try:
                nj = self.normalize(item)
                nj.provenance.generated_query = plan.generated_query
                nj.provenance.search_profile = plan.profile
                nj.provenance.technology_group = plan.technology_group
                nj.provenance.track = plan.track
                nj.provenance.matched_technology = plan.matched_technology
                jobs.append(nj)
            except Exception as exc:
                logger.debug("Instahyre normalize error: %s", exc)

        return jobs

    def normalize(self, raw: Any) -> NormalizedJob:
        if not isinstance(raw, dict):
            raise TypeError(f"Expected dict, got {type(raw)}")

        job_id = str(raw.get("id", raw.get("opportunity_id", "")) or "")
        slug = raw.get("slug", job_id)
        url = f"https://www.instahyre.com/job/{slug}/" if slug else ""
        company_data = raw.get("company", raw.get("employer", {})) or {}
        company = company_data.get("name", company_data) if isinstance(company_data, dict) else str(company_data)

        return NormalizedJob(
            provider=self.PROVIDER_NAME,
            provider_job_id=job_id,
            provider_name="Instahyre",
            provider_url=url,
            application_url=url,
            job_board="instahyre",
            company=str(company or ""),
            title=str(raw.get("designation", raw.get("title", "")) or ""),
            description=str(raw.get("description", raw.get("about", "")) or ""),
            skills=[str(s) for s in (raw.get("skills", []) or []) if s],
            technologies=[str(s) for s in (raw.get("skills", []) or []) if s],
            salary=str(raw.get("salary", raw.get("ctc", "")) or ""),
            experience=str(raw.get("experience", raw.get("min_experience", "")) or ""),
            location=str(raw.get("location", raw.get("city", "")) or ""),
            employment_type="full_time",
            remote_type="remote" if raw.get("is_remote") else "",
            posted_date=str(raw.get("posted_date", raw.get("created_at", "")) or "")[:10],
            provenance=JobProvenance(provider=self.PROVIDER_NAME, generated_query="", search_profile=""),
            provider_metadata={
                "company_size": company_data.get("employee_count", "") if isinstance(company_data, dict) else "",
                "funding": company_data.get("funding_stage", "") if isinstance(company_data, dict) else "",
            },
        )

    def shutdown(self) -> None:
        pass
