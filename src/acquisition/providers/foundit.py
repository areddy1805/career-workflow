"""
src/acquisition/providers/foundit.py — Foundit (formerly Monster India) provider.
Major Indian job board. No automatic application.
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


class FounditProvider(JobProvider):
    PROVIDER_NAME = "foundit"
    PROVIDER_TYPE = ProviderType.JOB_BOARD

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._initialized = True

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_auto_apply=False,
            authentication_required=False,
            supports_pagination=True,
            supports_location_filter=True,
            supports_experience_filter=True,
            supports_salary_filter=True,
            rate_limited=True,
            captcha_risk=True,
        )

    def health(self) -> ProviderHealth:
        return self._make_healthy()

    def search(self, plan: SearchPlan) -> list[NormalizedJob]:
        try:
            import requests
        except ImportError:
            return []

        params = {
            "query": plan.generated_query,
            "location": plan.location or "",
            "experience": plan.experience or 0,
            "page": 1,
            "limit": self._max_results(),
        }

        try:
            resp = requests.get(
                "https://www.foundit.in/middleware/jobsearch/",
                params=params,
                headers={"User-Agent": self._user_agent(), "Accept": "application/json"},
                timeout=(self._connect_timeout(), self._read_timeout()),
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("Foundit search failed: %s", exc)
            return []

        job_list = data.get("data", data.get("jobs", data)) if isinstance(data, dict) else data
        jobs = []
        for item in (job_list if isinstance(job_list, list) else [])[:self._max_results()]:
            try:
                nj = self.normalize(item)
                nj.provenance.generated_query = plan.generated_query
                nj.provenance.search_profile = plan.profile
                nj.provenance.technology_group = plan.technology_group
                nj.provenance.track = plan.track
                nj.provenance.matched_technology = plan.matched_technology
                jobs.append(nj)
            except Exception as exc:
                logger.debug("Foundit normalize error: %s", exc)

        return jobs

    def normalize(self, raw: Any) -> NormalizedJob:
        if not isinstance(raw, dict):
            raise TypeError(f"Expected dict, got {type(raw)}")

        job_id = str(raw.get("id", raw.get("jobId", raw.get("jd_id", ""))) or "")
        url = raw.get("jobUrl", raw.get("url", ""))
        if not url and job_id:
            url = f"https://www.foundit.in/job/{job_id}"

        salary_min = raw.get("minSalary", raw.get("min_salary", 0)) or 0
        salary_max = raw.get("maxSalary", raw.get("max_salary", 0)) or 0
        salary = ""
        if salary_min or salary_max:
            salary = f"₹{salary_min}L - ₹{salary_max}L" if salary_max else f"₹{salary_min}L+"

        return NormalizedJob(
            provider=self.PROVIDER_NAME,
            provider_job_id=job_id,
            provider_name="Foundit",
            provider_url=url,
            application_url=url,
            job_board="foundit",
            company=str(raw.get("company", raw.get("companyName", "")) or ""),
            title=str(raw.get("title", raw.get("jobTitle", "")) or ""),
            description=str(raw.get("description", raw.get("jobDescription", "")) or ""),
            skills=[str(s) for s in (raw.get("skills", raw.get("keySkills", [])) or []) if s],
            technologies=[],
            salary=salary,
            experience=str(raw.get("experience", raw.get("minExp", "")) or ""),
            location=str(raw.get("location", raw.get("city", "")) or ""),
            employment_type="full_time",
            remote_type="remote" if raw.get("isWfh") or raw.get("workFromHome") else "",
            posted_date=str(raw.get("postedDate", raw.get("created_at", "")) or "")[:10],
            provenance=JobProvenance(provider=self.PROVIDER_NAME, generated_query="", search_profile=""),
            provider_metadata={"company_type": raw.get("companyType", "")},
        )

    def shutdown(self) -> None:
        pass
