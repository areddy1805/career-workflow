"""
src/acquisition/providers/wellfound.py — Wellfound (AngelList Talent) provider.
Scrapes startup jobs. No automatic application.
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


class WellfoundProvider(JobProvider):
    PROVIDER_NAME = "wellfound"
    PROVIDER_TYPE = ProviderType.JOB_BOARD
    LIFECYCLE_STATE = "experimental"

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._initialized = True

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_auto_apply=False,
            authentication_required=False,
            supports_pagination=True,
            supports_location_filter=True,
            supports_remote_filter=True,
            rate_limited=True,
            captcha_risk=True,
        )

    def health(self) -> ProviderHealth:
        return self._make_healthy()

    def search(self, plan: SearchPlan) -> list[NormalizedJob]:
        """
        Wellfound job search via GraphQL API or scraping.
        Returns empty list when scraping is not configured/available.
        """
        try:
            return self._search_graphql(plan)
        except Exception as exc:
            logger.warning("Wellfound search failed: %s", exc)
            return []

    def normalize(self, raw: Any) -> NormalizedJob:
        if isinstance(raw, dict):
            return self._normalize_dict(raw)
        raise TypeError(f"Expected dict, got {type(raw)}")

    def shutdown(self) -> None:
        pass

    def _search_graphql(self, plan: SearchPlan) -> list[NormalizedJob]:
        """Wellfound public GraphQL endpoint for job listings."""
        try:
            import requests
        except ImportError:
            return []

        query = """
        query JobListings($query: String!, $locationSlugs: [String!], $remote: Boolean) {
          jobListings(query: $query, locationSlugs: $locationSlugs, remote: $remote, first: 20) {
            edges {
              node {
                id
                title
                description
                applyUrl
                jobUrl
                remote
                locationNames
                compensation
                jobType
                publishedAt
                startupConnection { startup { name } }
              }
            }
          }
        }
        """
        variables: dict = {"query": plan.generated_query}
        if plan.location:
            variables["locationSlugs"] = [plan.location.lower().replace(" ", "-")]
        if plan.remote_policy == "remote":
            variables["remote"] = True

        try:
            resp = requests.post(
                "https://api.wellfound.com/graphql",
                json={"query": query, "variables": variables},
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": self._user_agent(),
                },
                timeout=(self._connect_timeout(), self._read_timeout()),
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.debug("Wellfound GraphQL failed: %s", exc)
            return []

        edges = (data.get("data") or {}).get("jobListings", {}).get("edges", [])
        results = []
        for edge in edges:
            node = edge.get("node") or {}
            try:
                nj = self.normalize(node)
                nj.provenance.generated_query = plan.generated_query
                nj.provenance.search_profile = plan.profile
                nj.provenance.technology_group = plan.technology_group
                nj.provenance.track = plan.track
                nj.provenance.matched_technology = plan.matched_technology
                results.append(nj)
            except Exception as exc:
                logger.debug("Wellfound normalize error: %s", exc)

        return results[:self._max_results()]

    def _normalize_dict(self, raw: dict) -> NormalizedJob:
        job_id = str(raw.get("id", "") or "")
        company = (raw.get("startupConnection") or {}).get("startup", {}).get("name", "")
        title = raw.get("title", "")
        url = raw.get("jobUrl", raw.get("applyUrl", ""))
        apply_url = raw.get("applyUrl", url)
        locations = raw.get("locationNames", [])
        location = ", ".join(locations) if locations else ("Remote" if raw.get("remote") else "")

        return NormalizedJob(
            provider=self.PROVIDER_NAME,
            provider_job_id=job_id,
            provider_name="Wellfound",
            provider_url=url,
            application_url=apply_url,
            job_board="wellfound",
            company=str(company or ""),
            title=str(title or ""),
            description=str(raw.get("description", "") or ""),
            skills=[],
            technologies=[],
            salary=str(raw.get("compensation", "") or ""),
            experience="",
            location=location,
            employment_type=str(raw.get("jobType", "") or "").lower().replace(" ", "_"),
            remote_type="remote" if raw.get("remote") else "",
            posted_date=str(raw.get("publishedAt", "") or "")[:10],
            provenance=JobProvenance(provider=self.PROVIDER_NAME, generated_query="", search_profile=""),
            provider_metadata={"remote": raw.get("remote", False)},
        )
