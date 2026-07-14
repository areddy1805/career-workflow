"""
src/acquisition/providers/naukri.py — Naukri provider (Phase 0 migration).

This is the existing fetch_all_jobs() / acquire_jobs() logic migrated into
the provider framework. Functional behavior is IDENTICAL to the original code.
The Naukri-specific logic (challenge cooldown, nkparam, search cache) lives
entirely within this provider — the manager never sees any of it.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
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
from src.exceptions.exceptions import NaukriSearchChallengeError
from src.models.models import Job
from src.search.challenge_cooldown import SearchChallengeCooldown
from src.search.job_search_cache import JobSearchCache

logger = logging.getLogger(__name__)


class NaukriProvider(JobProvider):
    """
    Naukri.com job acquisition provider.

    Wraps NaukriLoginClient + NaukriJobClient, preserving all existing
    challenge-cooldown, search-cache, and rate-limiting behavior.

    This is the ONLY provider with supports_auto_apply=True.
    """

    PROVIDER_NAME = "naukri"
    PROVIDER_TYPE = ProviderType.JOB_BOARD

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._login_client = None
        self._job_client = None
        self._cache: JobSearchCache | None = None
        self._cooldown: SearchChallengeCooldown | None = None
        self._challenge_encountered = False
        self._search_requests_attempted = 0
        self._pages_stopped_low_yield = 0
        self._stop_reasons: dict[str, int] = {}
        self._initialized = True

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_auto_apply=True,
            supports_easy_apply=True,
            supports_resume_upload=True,
            supports_questionnaire=True,
            authentication_required=True,
            supports_login=True,
            supports_incremental=True,
            supports_pagination=True,
            supports_location_filter=True,
            supports_remote_filter=False,
            supports_salary_filter=True,
            supports_experience_filter=True,
            supports_company_filter=False,
            rate_limited=False,
            captcha_risk=True,
        )

    def health(self) -> ProviderHealth:
        if self._login_client is None:
            return ProviderHealth(
                provider=self.PROVIDER_NAME,
                status=ProviderHealthStatus.LOGIN_REQUIRED,
            )
        if self._challenge_encountered:
            return ProviderHealth(
                provider=self.PROVIDER_NAME,
                status=ProviderHealthStatus.CAPTCHA,
                last_challenge=datetime.now(timezone.utc).isoformat(),
            )
        return self._make_healthy()

    def search(self, plan: SearchPlan) -> list[NormalizedJob]:
        """
        Execute a single search plan against Naukri.

        Lazily initializes the login client on first call (same as before —
        login happens inside acquire(), not at provider init time).
        """
        self._ensure_clients()

        if self._cooldown and self._cooldown.is_active():
            logger.info("Naukri cooldown active — using cache")
            return self._from_cache(plan)

        return self._live_search(plan)

    def normalize(self, raw: Any) -> NormalizedJob:
        """Convert a raw Naukri Job object to NormalizedJob."""
        job: Job = raw
        job_id = str(getattr(job, "job_id", "") or "")

        return NormalizedJob(
            provider=self.PROVIDER_NAME,
            provider_job_id=job_id,
            provider_name="Naukri",
            provider_url=f"https://www.naukri.com/job-listings-{job_id}",
            application_url=getattr(job, "apply_link", "") or f"https://www.naukri.com/job-listings-{job_id}",
            job_board="naukri",
            company=job.company,
            title=job.title,
            description=job.description or "",
            skills=list(job.tags or []),
            technologies=[],
            salary=job.salary or "",
            experience=job.experience or "",
            location=job.location or "",
            employment_type="",
            remote_type="",
            posted_date=job.posted_date or "",
            provenance=JobProvenance(
                provider=self.PROVIDER_NAME,
                generated_query=getattr(job, "search_query", "") or "",
                search_profile=getattr(job, "search_profile", "") or "",
                technology_group=getattr(job, "matched_technology", "") or "",
                track=getattr(job, "search_track", "TIER_B") or "TIER_B",
                matched_technology=getattr(job, "matched_technology", "") or "",
            ),
            provider_metadata={
                "tags": list(job.tags or []),
                "acquisition_source": getattr(job, "acquisition_source", "live"),
            },
        )

    def shutdown(self) -> None:
        # Login clients don't require explicit teardown
        self._login_client = None
        self._job_client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_clients(self) -> None:
        """Lazy login — same behavior as the original pipeline acquire()."""
        if self._job_client is not None:
            return

        from src.client.job_client import NaukriJobClient
        from src.client.naukri_client import NaukriLoginClient

        username = os.environ.get("NAUKRI_USERNAME", "")
        password = os.environ.get("NAUKRI_PASSWORD", "")

        if not username or not password:
            raise RuntimeError(
                "NAUKRI_USERNAME and NAUKRI_PASSWORD must be set for Naukri provider"
            )

        login_client = NaukriLoginClient(username, password)
        login_client.login()

        self._login_client = login_client
        self._job_client = NaukriJobClient(login_client)

        cache_path = os.getenv("JOB_SEARCH_CACHE_PATH", "data/job_search_cache.json")
        ttl = int(os.getenv("JOB_SEARCH_CACHE_TTL_DAYS", "3"))
        self._cache = JobSearchCache(path=cache_path, ttl_days=ttl)

        cooldown_path = os.getenv("SEARCH_CHALLENGE_STATE_PATH", "data/search_challenge_state.json")
        cooldown_mins = int(os.getenv("SEARCH_CHALLENGE_COOLDOWN_MINUTES", "60"))
        self._cooldown = SearchChallengeCooldown(
            path=cooldown_path, cooldown_minutes=cooldown_mins
        )

    def _live_search(self, plan: SearchPlan) -> list[NormalizedJob]:
        """
        Execute a live Naukri search for this plan.
        Replicates the fetch_all_jobs() loop for a single query.
        """
        if self._challenge_encountered:
            return []

        jc = self._job_client
        query = plan.generated_query
        location = plan.location
        experience = plan.experience

        PAGES = self._max_pages()
        JOB_AGE = int(os.getenv("SEARCH_JOB_AGE_DAYS", "3"))
        RESULTS_PER_PAGE = int(os.getenv("SEARCH_RESULTS_PER_PAGE", "20"))
        min_new_yield = int(os.getenv("SEARCH_MIN_NEW_JOBS_PER_PAGE", "2"))
        low_yield_patience = int(os.getenv("SEARCH_LOW_YIELD_PATIENCE", "1"))

        collected: list[NormalizedJob] = []
        seen_ids: set[str] = set()
        previous_page_signature = None
        consecutive_low_yield = 0

        for page in range(1, PAGES + 1):
            try:
                self._search_requests_attempted += 1
                raw_jobs = jc.search_jobs(
                    keyword=query,
                    location=location,
                    experience=experience,
                    job_age=JOB_AGE,
                    page=page,
                    results_per_page=RESULTS_PER_PAGE,
                )

                page_sig = tuple(
                    str(getattr(j, "id", None) or getattr(j, "job_id", None) or "")
                    for j in raw_jobs
                )

                if raw_jobs and page_sig == previous_page_signature:
                    break
                previous_page_signature = page_sig

                new_count = 0
                for raw_job in raw_jobs:
                    job_id = str(
                        getattr(raw_job, "id", None)
                        or getattr(raw_job, "job_id", None)
                        or ""
                    )
                    if job_id and job_id in seen_ids:
                        continue
                    if job_id:
                        seen_ids.add(job_id)

                    # Tag search context onto raw job so normalize() can read it
                    setattr(raw_job, "search_query", query)
                    setattr(raw_job, "search_profile", plan.profile)
                    setattr(raw_job, "matched_technology", plan.matched_technology)
                    setattr(raw_job, "search_track", plan.track)
                    setattr(raw_job, "acquisition_source", "live")

                    collected.append(self.normalize(raw_job))
                    new_count += 1

                if not raw_jobs or len(raw_jobs) < RESULTS_PER_PAGE:
                    self._stop_reasons["short_page"] = self._stop_reasons.get("short_page", 0) + 1
                    break

                if new_count < min_new_yield:
                    consecutive_low_yield += 1
                else:
                    consecutive_low_yield = 0

                if page < PAGES and consecutive_low_yield >= low_yield_patience:
                    self._pages_stopped_low_yield += 1
                    self._stop_reasons["low_yield"] = self._stop_reasons.get("low_yield", 0) + 1
                    break

                time.sleep(float(os.getenv("SEARCH_REQUEST_DELAY_SECONDS", "1.2")))

            except NaukriSearchChallengeError as exc:
                self._challenge_encountered = True
                if self._cooldown:
                    self._cooldown.record_challenge()
                logger.warning("Naukri search challenge: %s", exc)
                break

            except Exception as exc:
                logger.warning("Naukri search error: query=%s exp=%d p=%d -> %s", query, experience, page, exc)
                time.sleep(3)

        return collected

    def _from_cache(self, plan: SearchPlan) -> list[NormalizedJob]:
        """Return jobs from cache when cooldown is active."""
        if self._cache is None:
            return []
        cached = self._cache.load()
        return [self.normalize(j) for j in cached]

    def get_login_client(self):
        """Expose login client for the pipeline's reconcile/apply stages."""
        return self._login_client

    def get_job_client(self):
        """Expose job client for the pipeline's classify/apply stages."""
        return self._job_client

    def get_fetch_result_metadata(self) -> dict:
        """Return metadata compatible with the original JobFetchResult for the pipeline."""
        return {
            "challenge_encountered": self._challenge_encountered,
            "search_requests_attempted": self._search_requests_attempted,
            "pages_stopped_low_yield": self._pages_stopped_low_yield,
            "stop_reasons": self._stop_reasons,
            "search_skipped_due_to_cooldown": bool(
                self._cooldown and self._cooldown.is_active()
            ),
        }
