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


class ArbeitnowProvider(JobProvider):
    PROVIDER_NAME = "arbeitnow"
    PROVIDER_TYPE = ProviderType.API
    LIFECYCLE_STATE = "production"

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._base_url = "https://www.arbeitnow.com/api/job-board-api"
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self._user_agent()})

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            native_apply=False,
            external_apply=True,
            manual_only=False,
            playwright_supported=False,
            supports_location_filter=True, 
            supports_remote_filter=True,
            supports_pagination=True,
        )

    def health(self) -> ProviderHealth:
        try:
            resp = self._session.get(self._base_url, timeout=self._connect_timeout())
            if resp.status_code == 200:
                return self._make_healthy()
            return self._make_unavailable_health(f"HTTP {resp.status_code}")
        except Exception as exc:
            return self._make_unavailable_health(str(exc))

    def search(self, plan: SearchPlan) -> list[NormalizedJob]:
        # Arbeitnow API doesn't support query params for search effectively.
        # We will fetch page 1 and filter locally for demonstration.
        try:
            resp = self._session.get(self._base_url, timeout=self._read_timeout())
            resp.raise_for_status()
            data = resp.json()
            jobs = data.get("data", [])
            
            normalized = []
            query_lower = plan.generated_query.lower() if plan.generated_query else ""
            
            for j in jobs:
                # Basic local filtering
                title = j.get("title", "").lower()
                company = j.get("company_name", "").lower()
                
                if query_lower and query_lower not in title and query_lower not in company:
                    continue
                    
                nj = self.normalize(j)
                nj.provenance.provider = self.PROVIDER_NAME
                nj.provenance.generated_query = plan.generated_query
                nj.provenance.search_profile = plan.profile
                nj.provenance.matched_technology = plan.matched_technology
                normalized.append(nj)
                
            return normalized
        except Exception as exc:
            logger.warning(f"Arbeitnow search failed: {exc}")
            return []

    def normalize(self, raw: dict[str, Any]) -> NormalizedJob:
        return NormalizedJob(
            provider=self.PROVIDER_NAME,
            provider_job_id=str(raw.get("slug", "")),
            provider_name="Arbeitnow",
            provider_url=raw.get("url", ""),
            application_url=raw.get("url", ""),
            job_board="arbeitnow",
            company=raw.get("company_name", ""),
            title=raw.get("title", ""),
            description=raw.get("description", ""),
            location=raw.get("location", ""),
            employment_type=raw.get("job_types", [""])[0] if raw.get("job_types") else "",
            posted_date=str(raw.get("created_at", "")),
            remote_type="remote" if raw.get("remote") else "onsite",
            provider_metadata={
                "tags": raw.get("tags", [])
            }
        )

    def shutdown(self) -> None:
        if hasattr(self, "_session"):
            self._session.close()
