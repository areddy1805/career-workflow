import logging
import time
from typing import Any
import requests
import re

from src.acquisition.models import (
    NormalizedJob,
    ProviderCapabilities,
    ProviderHealth,
    ProviderType,
    SearchPlan,
)
from src.acquisition.provider import JobProvider

logger = logging.getLogger(__name__)


class HackerNewsProvider(JobProvider):
    PROVIDER_NAME = "hackernews"
    PROVIDER_TYPE = ProviderType.JOB_BOARD
    LIFECYCLE_STATE = "production"

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._base_url = "https://hn.algolia.com/api/v1/search"
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self._user_agent()})

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_auto_apply=False,
            supports_location_filter=True,
            supports_remote_filter=True,
            supports_pagination=True,
        )

    def health(self) -> ProviderHealth:
        try:
            resp = self._session.get(f"{self._base_url}?query=who+is+hiring", timeout=self._connect_timeout())
            if resp.status_code == 200:
                return self._make_healthy()
            return self._make_unavailable_health(f"HTTP {resp.status_code}")
        except Exception as exc:
            return self._make_unavailable_health(str(exc))

    def search(self, plan: SearchPlan) -> list[NormalizedJob]:
        params = {
            "query": f'"who is hiring" {plan.generated_query}',
            "tags": "comment",
            "hitsPerPage": self._max_results()
        }
        
        try:
            resp = self._session.get(self._base_url, params=params, timeout=self._read_timeout())
            resp.raise_for_status()
            data = resp.json()
            jobs = data.get("hits", [])
            
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
            logger.warning(f"HackerNews search failed: {exc}")
            return []

    def normalize(self, raw: dict[str, Any]) -> NormalizedJob:
        text = raw.get("comment_text", "")
        # Basic parsing attempt for HN posts
        company = "Unknown"
        title = "Hacker News Job"
        
        # First line usually contains Company | Title | Location
        lines = [line.strip() for line in re.sub(r'<[^>]+>', '', text).split('\n') if line.strip()]
        if lines:
            header = lines[0]
            parts = [p.strip() for p in header.split('|')]
            if len(parts) >= 1:
                company = parts[0]
            if len(parts) >= 2:
                title = parts[1]
                
        object_id = str(raw.get("objectID", ""))
        url = f"https://news.ycombinator.com/item?id={object_id}"
        
        return NormalizedJob(
            provider=self.PROVIDER_NAME,
            provider_job_id=object_id,
            provider_name="Hacker News",
            provider_url=url,
            application_url=url,
            job_board="hackernews",
            company=company,
            title=title,
            description=text,
            posted_date=raw.get("created_at", ""),
            provider_metadata={
                "author": raw.get("author", ""),
                "points": raw.get("points", 0)
            }
        )

    def shutdown(self) -> None:
        if hasattr(self, "_session"):
            self._session.close()
