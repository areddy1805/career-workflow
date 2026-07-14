"""
src/acquisition/providers/weworkremotely.py — We Work Remotely provider.

Scrapes the RSS feed at https://weworkremotely.com/remote-jobs.rss
No authentication required.
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
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

_RSS_URL = "https://weworkremotely.com/remote-jobs.rss"


class WeWorkRemotelyProvider(JobProvider):
    """
    We Work Remotely provider via RSS feed.
    Filters RSS items against the search plan keywords.
    """

    PROVIDER_NAME = "weworkremotely"
    PROVIDER_TYPE = ProviderType.JOB_BOARD

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._initialized = True
        self._cached_items: list[dict] = []
        self._cached_at: float = 0.0

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_auto_apply=False,
            authentication_required=False,
            supports_login=False,
            supports_pagination=False,
            supports_location_filter=False,
            supports_remote_filter=True,
            rate_limited=False,
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
        try:
            items = self._fetch_rss()
        except Exception as exc:
            logger.warning("WWR fetch failed: %s", exc)
            return []

        query_terms = set(plan.generated_query.lower().split())
        matched = []

        for item in items:
            if self._matches(item, query_terms):
                try:
                    nj = self.normalize(item)
                    nj.provenance.generated_query = plan.generated_query
                    nj.provenance.search_profile = plan.profile
                    nj.provenance.technology_group = plan.technology_group
                    nj.provenance.track = plan.track
                    nj.provenance.matched_technology = plan.matched_technology
                    matched.append(nj)
                except Exception as exc:
                    logger.debug("WWR normalize error: %s", exc)

        return matched[:self._max_results()]

    def normalize(self, raw: Any) -> NormalizedJob:
        item: dict = raw
        link = item.get("link", "")
        guid = item.get("guid", link)
        job_id = re.sub(r"[^a-zA-Z0-9_-]", "_", guid)[-80:]

        # WWR title format can be "Category: Company - Title", "Company: Title", or "Company - Title"
        raw_title = item.get("title", "")
        company = ""
        title = raw_title
        
        if ": " in raw_title:
            parts = raw_title.split(": ", 1)
            # If the part after ":" has a " - ", then parts[0] might be category.
            # But let's simplify: usually it's "Company: Title" or "Category: Company - Title"
            if " - " in parts[1]:
                subparts = parts[1].split(" - ", 1)
                company = subparts[0].strip()
                title = subparts[1].strip()
            else:
                company = parts[0].strip()
                title = parts[1].strip()
        elif " - " in raw_title:
            parts = raw_title.split(" - ", 1)
            company = parts[0].strip()
            title = parts[1].strip()
            
        if not company:
            company = "Unknown"

        published = item.get("pubDate", "")
        posted_date = ""
        if published:
            try:
                from email.utils import parsedate_to_datetime
                posted_date = parsedate_to_datetime(published).strftime("%Y-%m-%d")
            except Exception:
                posted_date = published[:10] if len(published) >= 10 else published

        description = re.sub(r"<[^>]+>", " ", item.get("description", ""))
        description = re.sub(r"\s+", " ", description).strip()

        return NormalizedJob(
            provider=self.PROVIDER_NAME,
            provider_job_id=job_id,
            provider_name="We Work Remotely",
            provider_url=link,
            application_url=link,
            job_board="weworkremotely",
            company=company,
            title=title,
            description=description,
            skills=[],
            technologies=[],
            salary="",
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
                "category": item.get("category", ""),
                "guid": guid,
            },
        )

    def shutdown(self) -> None:
        pass

    def _fetch_rss(self) -> list[dict]:
        import time
        now = time.time()
        if self._cached_items and (now - self._cached_at) < 300:
            return self._cached_items

        headers = {"User-Agent": self._user_agent()}
        resp = requests.get(
            _RSS_URL, headers=headers,
            timeout=(self._connect_timeout(), self._read_timeout()),
        )
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
        items = []
        for item_el in root.findall(".//item"):
            entry = {}
            for child in item_el:
                tag = child.tag.split("}")[-1]  # strip namespace
                entry[tag] = child.text or ""
            items.append(entry)

        self._cached_items = items
        self._cached_at = now
        logger.debug("WWR RSS returned %d items", len(items))
        return items

    def _matches(self, item: dict, query_terms: set[str]) -> bool:
        if not query_terms:
            return True
        searchable = " ".join([
            item.get("title", ""),
            item.get("description", "")[:300],
        ]).lower()
        return any(term in searchable for term in query_terms)
