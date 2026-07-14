import logging
import time
from typing import Any
import requests

from src.acquisition.models import (
    NormalizedJob,
    ProviderCapabilities,
    ProviderHealth,
    ProviderType,
    SearchPlan,
)
from src.acquisition.provider import JobProvider

logger = logging.getLogger(__name__)


class RemotiveProvider(JobProvider):
    PROVIDER_NAME = "remotive"
    PROVIDER_TYPE = ProviderType.API
    LIFECYCLE_STATE = "production"

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._base_url = "https://remotive.com/api/remote-jobs"
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self._user_agent()})

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            native_apply=False,
            external_apply=True,
            manual_only=False,
            playwright_supported=False,
            supports_location_filter=False, # Remotive is remote-only
            supports_remote_filter=True,
            supports_pagination=False, # Returns all in one payload typically
        )

    def health(self) -> ProviderHealth:
        try:
            resp = self._session.get(f"{self._base_url}?limit=1", timeout=self._connect_timeout())
            if resp.status_code == 200:
                return self._make_healthy()
            return self._make_unavailable_health(f"HTTP {resp.status_code}")
        except Exception as exc:
            return self._make_unavailable_health(str(exc))

    def search(self, plan: SearchPlan) -> list[NormalizedJob]:
        params = {}
        if plan.generated_query:
            params["search"] = plan.generated_query
            
        try:
            resp = self._session.get(self._base_url, params=params, timeout=self._read_timeout())
            resp.raise_for_status()
            data = resp.json()
            jobs = data.get("jobs", [])
            
            normalized = []
            for j in jobs:
                nj = self.normalize(j)
                nj.provenance.provider = self.PROVIDER_NAME
                nj.provenance.generated_query = plan.generated_query
                nj.provenance.search_profile = plan.profile
                nj.provenance.matched_technology = plan.matched_technology
                normalized.append(nj)
                
            return normalized
        except Exception as exc:
            logger.warning(f"Remotive search failed: {exc}")
            return []

    def normalize(self, raw: dict[str, Any]) -> NormalizedJob:
        return NormalizedJob(
            provider=self.PROVIDER_NAME,
            provider_job_id=str(raw.get("id", "")),
            provider_name="Remotive",
            provider_url=raw.get("url", ""),
            application_url=raw.get("url", ""),
            job_board="remotive",
            company=raw.get("company_name", ""),
            title=raw.get("title", ""),
            description=raw.get("description", ""),
            location=raw.get("candidate_required_location", ""),
            employment_type=raw.get("job_type", ""),
            posted_date=raw.get("publication_date", ""),
            remote_type="remote",
            provider_metadata={
                "category": raw.get("category", ""),
                "tags": raw.get("tags", [])
            }
        )

    def shutdown(self) -> None:
        if hasattr(self, "_session"):
            self._session.close()
