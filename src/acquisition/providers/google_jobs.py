"""
src/acquisition/providers/google_jobs.py — Google Jobs provider.

Backend is configurable via YAML:
  backend: playwright   (default — Playwright-based scraping, no API key)
  backend: serpapi      (SerpAPI — requires SERPAPI_KEY env var)
  backend: manual       (disabled, jobs entered manually)

No automatic application. All jobs → External Apply queue.
"""
from __future__ import annotations

import logging
import re
from typing import Any

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


class GoogleJobsProvider(JobProvider):
    """
    Google Jobs acquisition provider.

    Captures: original URL, company, title, location, salary,
    employment type, remote status, posted date, description.
    """

    PROVIDER_NAME = "google_jobs"
    PROVIDER_TYPE = ProviderType.AGGREGATOR
    LIFECYCLE_STATE = "experimental"

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._backend = config.get("backend", "playwright")
        self._initialized = True

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_auto_apply=False,
            authentication_required=False,
            supports_login=False,
            supports_pagination=True,
            supports_location_filter=True,
            supports_remote_filter=True,
            supports_salary_filter=False,
            supports_experience_filter=False,
            rate_limited=True,
            captcha_risk=True,
        )

    def health(self) -> ProviderHealth:
        if self._backend == "manual":
            return ProviderHealth(
                provider=self.PROVIDER_NAME,
                status=ProviderHealthStatus.DISABLED,
                error="Backend set to 'manual'",
            )
        if self._backend == "serpapi":
            import os
            if not os.environ.get("SERPAPI_KEY"):
                return ProviderHealth(
                    provider=self.PROVIDER_NAME,
                    status=ProviderHealthStatus.UNAVAILABLE,
                    error="SERPAPI_KEY env var not set",
                )
        return self._make_healthy()

    def search(self, plan: SearchPlan) -> list[NormalizedJob]:
        if self._backend == "manual":
            return []
        if self._backend == "serpapi":
            return self._search_serpapi(plan)
        return self._search_playwright(plan)

    def normalize(self, raw: Any) -> NormalizedJob:
        if isinstance(raw, dict):
            return self._normalize_dict(raw)
        raise TypeError(f"GoogleJobsProvider.normalize expects dict, got {type(raw)}")

    def shutdown(self) -> None:
        pass

    # ------------------------------------------------------------------
    # SerpAPI backend
    # ------------------------------------------------------------------

    def _search_serpapi(self, plan: SearchPlan) -> list[NormalizedJob]:
        import os
        try:
            import requests
        except ImportError:
            logger.warning("requests not installed — cannot use SerpAPI backend")
            return []

        api_key = os.environ.get("SERPAPI_KEY", "")
        if not api_key:
            logger.warning("SERPAPI_KEY not set")
            return []

        params = {
            "engine": "google_jobs",
            "q": plan.generated_query,
            "location": plan.location or "",
            "api_key": api_key,
            "num": self._max_results(),
        }
        if plan.country:
            params["gl"] = plan.country.lower()

        try:
            resp = requests.get(
                "https://serpapi.com/search",
                params=params,
                timeout=(self._connect_timeout(), self._read_timeout()),
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("SerpAPI request failed: %s", exc)
            return []

        results = []
        for item in data.get("jobs_results", []):
            try:
                nj = self.normalize(item)
                nj.provenance.generated_query = plan.generated_query
                nj.provenance.search_profile = plan.profile
                nj.provenance.technology_group = plan.technology_group
                nj.provenance.track = plan.track
                nj.provenance.matched_technology = plan.matched_technology
                results.append(nj)
            except Exception as exc:
                logger.debug("SerpAPI normalize error: %s", exc)

        return results

    # ------------------------------------------------------------------
    # Playwright backend
    # ------------------------------------------------------------------

    def _search_playwright(self, plan: SearchPlan) -> list[NormalizedJob]:
        """
        Playwright-based Google Jobs scraping.
        Returns structured job dicts extracted from the Google Jobs UI.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning(
                "playwright not installed — install with: pip install playwright && playwright install chromium"
            )
            return []

        query = plan.generated_query
        location = plan.location or ""
        search_query = f"{query} {location}".strip() if location else query
        url = f"https://www.google.com/search?q={requests_quote(search_query)}+jobs&ibp=htl;jobs"

        results: list[NormalizedJob] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                ctx = browser.new_context(user_agent=self._user_agent())
                page = ctx.new_page()

                page.goto(url, timeout=self._read_timeout() * 1000)
                page.wait_for_timeout(2000)

                # Extract job cards from Google Jobs embedded panel
                job_cards = page.query_selector_all('[data-ved][data-cid]')

                for card in job_cards[:self._max_results()]:
                    try:
                        raw = self._extract_card(card, page)
                        if raw:
                            nj = self.normalize(raw)
                            nj.provenance.generated_query = plan.generated_query
                            nj.provenance.search_profile = plan.profile
                            nj.provenance.technology_group = plan.technology_group
                            nj.provenance.track = plan.track
                            nj.provenance.matched_technology = plan.matched_technology
                            results.append(nj)
                    except Exception as exc:
                        logger.debug("Google Jobs card extraction error: %s", exc)

                browser.close()

        except Exception as exc:
            logger.warning("Google Jobs Playwright search failed: %s", exc)

        logger.debug("Google Jobs Playwright returned %d jobs for '%s'", len(results), query)
        return results

    def _extract_card(self, card, page) -> dict | None:
        """Extract structured data from a Google Jobs card element."""
        try:
            title_el = card.query_selector("h2, [data-jobid]")
            title = title_el.inner_text().strip() if title_el else ""

            company_el = card.query_selector(".vNEEBe, [class*='company']")
            company = company_el.inner_text().strip() if company_el else ""

            location_el = card.query_selector(".Qk80Jf, [class*='location']")
            location = location_el.inner_text().strip() if location_el else ""

            link_el = card.query_selector("a[href]")
            url = link_el.get_attribute("href") if link_el else ""
            if url and url.startswith("/"):
                url = "https://www.google.com" + url

            if not title:
                return None

            return {
                "title": title,
                "company_name": company,
                "location": location,
                "job_id": hash(f"{company}|{title}|{location}"),
                "job_highlights": [],
                "description": "",
                "detected_extensions": {},
                "apply_options": [{"link": url}] if url else [],
                "via": "Google Jobs",
            }
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Normalization (handles both SerpAPI and Playwright dicts)
    # ------------------------------------------------------------------

    def _normalize_dict(self, raw: dict) -> NormalizedJob:
        job_id = str(raw.get("job_id", raw.get("id", "")) or "")
        if not job_id:
            # Stable ID from company+title
            job_id = str(abs(hash(f"{raw.get('company_name','')}|{raw.get('title','')}")))

        title = raw.get("title", raw.get("position", ""))
        company = raw.get("company_name", raw.get("company", ""))
        location = raw.get("location", "")

        # Description from highlights + description field
        highlights = raw.get("job_highlights", [])
        desc_parts = []
        for hl in highlights:
            if isinstance(hl, dict):
                label = hl.get("title", "")
                items = hl.get("items", [])
                if label:
                    desc_parts.append(f"**{label}**")
                desc_parts.extend(items)
        if raw.get("description"):
            desc_parts.append(raw["description"])
        description = "\n".join(str(p) for p in desc_parts)

        # Application URL — prefer direct apply link
        apply_url = ""
        apply_options = raw.get("apply_options", [])
        if apply_options and isinstance(apply_options, list):
            apply_url = apply_options[0].get("link", "") if apply_options else ""
        if not apply_url:
            apply_url = raw.get("job_apply_link", "")

        provider_url = apply_url  # Google Jobs links go directly to application

        # Extended fields from detected_extensions
        ext = raw.get("detected_extensions", {})
        posted_date = str(ext.get("posted_at", raw.get("posted_at", "")) or "")
        employment_type = str(ext.get("schedule_type", raw.get("employment_type", "")) or "")
        salary = str(ext.get("salary", raw.get("salary", "")) or "")
        work_from_home = ext.get("work_from_home", False)

        return NormalizedJob(
            provider=self.PROVIDER_NAME,
            provider_job_id=job_id,
            provider_name="Google Jobs",
            provider_url=provider_url,
            application_url=apply_url or provider_url,
            job_board="google_jobs",
            company=str(company or ""),
            title=str(title or ""),
            description=description,
            skills=[],
            technologies=[],
            salary=salary,
            experience="",
            location=str(location or ""),
            employment_type=employment_type.lower().replace(" ", "_"),
            remote_type="remote" if work_from_home else "",
            posted_date=posted_date,
            provenance=JobProvenance(
                provider=self.PROVIDER_NAME,
                generated_query="",
                search_profile="",
            ),
            provider_metadata={
                "via": raw.get("via", "Google Jobs"),
                "thumbnail": raw.get("thumbnail", ""),
                "apply_options": apply_options,
                "extensions": ext,
            },
        )


def requests_quote(s: str) -> str:
    """URL-encode a string without importing urllib at module level."""
    try:
        from urllib.parse import quote_plus
        return quote_plus(s)
    except Exception:
        return s.replace(" ", "+")
