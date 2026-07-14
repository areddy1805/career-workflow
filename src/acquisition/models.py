"""
src/acquisition/models.py — Canonical provider-agnostic data models.

The entire acquisition layer speaks these types.
Nothing below acquisition should import from here — the normalizer bridges
NormalizedJob → Job (src/models/models.py) at the pipeline boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ProviderType(str, Enum):
    """Taxonomy of job source types. Reserved for future routing/display."""
    JOB_BOARD  = "job_board"
    AGGREGATOR = "aggregator"
    ATS        = "ats"
    REFERRAL   = "referral"
    COMPANY    = "company"
    RSS        = "rss"
    API        = "api"


class ProviderHealthStatus(str, Enum):
    """Operational status of a provider at query time."""
    HEALTHY        = "healthy"
    RATE_LIMITED   = "rate_limited"
    CAPTCHA        = "captcha"
    LOGIN_REQUIRED = "login_required"
    DISABLED       = "disabled"
    MAINTENANCE    = "maintenance"
    UNAVAILABLE    = "unavailable"


class ProviderPriority(str, Enum):
    """Human-readable priority for config YAMLs. Manager maps to int."""
    CRITICAL = "critical"
    HIGH     = "high"
    NORMAL   = "normal"
    LOW      = "low"

    def to_int(self) -> int:
        return {"critical": 0, "high": 1, "normal": 2, "low": 3}[self.value]


# ---------------------------------------------------------------------------
# Capability Matrix
# ---------------------------------------------------------------------------


@dataclass
class ProviderCapabilities:
    """
    Full capability matrix for a provider.
    Rendered as a ✓/✗ matrix in the dashboard UI.
    Used by AcquisitionManager to route applications correctly.
    """
    # Application capabilities
    supports_auto_apply: bool = False
    supports_easy_apply: bool = False
    supports_resume_upload: bool = False
    supports_questionnaire: bool = False

    # Auth capabilities
    authentication_required: bool = False
    supports_login: bool = False

    # Search capabilities
    supports_incremental: bool = False
    supports_pagination: bool = True

    # Filter capabilities
    supports_location_filter: bool = True
    supports_remote_filter: bool = False
    supports_salary_filter: bool = False
    supports_experience_filter: bool = False
    supports_company_filter: bool = False

    # Risk profile
    rate_limited: bool = False
    captcha_risk: bool = False

    def to_dict(self) -> dict:
        return {
            "supports_auto_apply": self.supports_auto_apply,
            "supports_easy_apply": self.supports_easy_apply,
            "supports_resume_upload": self.supports_resume_upload,
            "supports_questionnaire": self.supports_questionnaire,
            "authentication_required": self.authentication_required,
            "supports_login": self.supports_login,
            "supports_incremental": self.supports_incremental,
            "supports_pagination": self.supports_pagination,
            "supports_location_filter": self.supports_location_filter,
            "supports_remote_filter": self.supports_remote_filter,
            "supports_salary_filter": self.supports_salary_filter,
            "supports_experience_filter": self.supports_experience_filter,
            "supports_company_filter": self.supports_company_filter,
            "rate_limited": self.rate_limited,
            "captcha_risk": self.captcha_risk,
        }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@dataclass
class ProviderHealth:
    """Runtime health snapshot for one provider."""
    provider: str
    status: ProviderHealthStatus
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    latency_ms: float = 0.0
    error: str = ""
    # Extended stats
    last_successful_search: str = ""
    last_failure: str = ""
    last_challenge: str = ""
    searches_total: int = 0
    searches_success: int = 0
    searches_failed: int = 0

    @property
    def success_pct(self) -> float:
        if not self.searches_total:
            return 0.0
        return round(self.searches_success / self.searches_total * 100, 1)

    @property
    def failure_pct(self) -> float:
        if not self.searches_total:
            return 0.0
        return round(self.searches_failed / self.searches_total * 100, 1)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "status": self.status.value,
            "checked_at": self.checked_at,
            "latency_ms": round(self.latency_ms, 1),
            "error": self.error,
            "last_successful_search": self.last_successful_search,
            "last_failure": self.last_failure,
            "last_challenge": self.last_challenge,
            "searches_total": self.searches_total,
            "searches_success": self.searches_success,
            "searches_failed": self.searches_failed,
            "success_pct": self.success_pct,
            "failure_pct": self.failure_pct,
        }


# ---------------------------------------------------------------------------
# SearchPlan
# ---------------------------------------------------------------------------


@dataclass
class SearchPlan:
    """
    Provider-agnostic search plan generated by SearchPlanner.

    Richer than a flat query dict — carries enough context for any provider
    to apply its own filters. Fields not supported by a provider are ignored.
    """
    # Core identity
    profile: str
    generated_query: str
    location: str

    # Geographic context
    country: str = ""

    # Experience
    experience: int = 0                  # years, 0 = unspecified

    # Work mode hints
    work_mode: str = ""                  # "remote", "hybrid", "onsite", ""
    remote_policy: str = ""              # provider-agnostic policy string

    # Compensation
    salary_range: dict[str, Any] = field(default_factory=dict)  # {min, max, currency}

    # Provider targeting
    target_providers: list[str] = field(default_factory=list)   # [] = all enabled
    provider_filters: dict[str, Any] = field(default_factory=dict)   # per-provider filter overrides
    provider_overrides: dict[str, Any] = field(default_factory=dict) # per-provider config overrides

    # Ranking
    priority: ProviderPriority = ProviderPriority.NORMAL
    weight: float = 1.0

    # Search context (for provenance)
    track: str = "TIER_B"
    matched_technology: str = ""
    technology_group: str = ""          # tech profile name (e.g. "python_ai", "node_backend")

    # Arbitrary metadata preserved through to provenance
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Job Provenance
# ---------------------------------------------------------------------------


@dataclass
class JobProvenance:
    """
    Full audit trail: why was this job discovered?

    Embedded in every NormalizedJob. Survives deduplication (merged).
    Enables answering "why did we find this?" years later.
    """
    provider: str
    generated_query: str
    search_profile: str
    technology_group: str = ""
    track: str = ""
    matched_technology: str = ""
    acquired_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    planner_version: str = "3.1"
    pipeline_version: str = "3.1"
    # All providers that also returned this job (cross-provider duplicates)
    also_seen_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "generated_query": self.generated_query,
            "search_profile": self.search_profile,
            "technology_group": self.technology_group,
            "track": self.track,
            "matched_technology": self.matched_technology,
            "acquired_at": self.acquired_at,
            "planner_version": self.planner_version,
            "pipeline_version": self.pipeline_version,
            "also_seen_on": self.also_seen_on,
        }


# ---------------------------------------------------------------------------
# NormalizedJob
# ---------------------------------------------------------------------------


@dataclass
class NormalizedJob:
    """
    Canonical, provider-agnostic job record.

    Every provider must return this model.
    Nothing below acquisition should know which provider produced a job.
    """
    # Provider identity
    provider: str                        # e.g. "naukri", "google_jobs"
    provider_job_id: str                 # raw ID from the source
    provider_name: str                   # human-readable provider name
    provider_url: str                    # URL of listing on provider's site
    application_url: str                 # URL to apply (may differ)
    job_board: str                       # board name

    # Job content
    company: str
    title: str
    description: str = ""
    skills: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    salary: str = ""
    experience: str = ""
    location: str = ""
    employment_type: str = ""            # "full_time", "contract", "part_time"
    remote_type: str = ""               # "remote", "hybrid", "onsite"
    posted_date: str = ""

    # Provenance (always populated)
    provenance: JobProvenance = field(default_factory=lambda: JobProvenance(
        provider="unknown", generated_query="", search_profile=""
    ))

    # Provider-specific extra data — NEVER read by downstream pipeline
    # On deduplication, this is MERGED from all matching providers
    provider_metadata: dict[str, Any] = field(default_factory=dict)

    # Acquisition timestamp (top-level for quick access)
    acquired_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# Stats & Summary
# ---------------------------------------------------------------------------


@dataclass
class ProviderRunStats:
    """Stats collected for one provider during a single acquisition run."""
    provider: str
    provider_type: str = ProviderType.JOB_BOARD.value
    searches_executed: int = 0
    jobs_returned: int = 0
    unique_jobs: int = 0
    duplicates_removed: int = 0
    failures: int = 0
    latency_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_successful_search: str = ""
    last_failure: str = ""
    last_challenge: str = ""

    @property
    def success_pct(self) -> float:
        total = self.searches_executed
        if not total:
            return 0.0
        return round((total - self.failures) / total * 100, 1)

    @property
    def failure_pct(self) -> float:
        total = self.searches_executed
        if not total:
            return 0.0
        return round(self.failures / total * 100, 1)

    @property
    def cache_pct(self) -> float:
        total = self.cache_hits + self.cache_misses
        if not total:
            return 0.0
        return round(self.cache_hits / total * 100, 1)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "provider_type": self.provider_type,
            "searches_executed": self.searches_executed,
            "jobs_returned": self.jobs_returned,
            "unique_jobs": self.unique_jobs,
            "duplicates_removed": self.duplicates_removed,
            "failures": self.failures,
            "latency_ms": round(self.latency_ms, 1),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "success_pct": self.success_pct,
            "failure_pct": self.failure_pct,
            "cache_pct": self.cache_pct,
            "last_successful_search": self.last_successful_search,
            "last_failure": self.last_failure,
            "last_challenge": self.last_challenge,
        }


@dataclass
class AcquisitionSummary:
    """Full summary of an acquisition run across all providers."""
    provider_stats: list[ProviderRunStats] = field(default_factory=list)
    cross_provider_duplicates: int = 0
    total_unique_jobs: int = 0
    total_jobs_returned: int = 0
    new_jobs: int = 0                  # not seen in cache from previous runs

    @property
    def coverage_pct(self) -> float:
        """% of providers that returned at least one job."""
        active = [s for s in self.provider_stats if s.searches_executed > 0]
        if not active:
            return 0.0
        successful = [s for s in active if s.unique_jobs > 0]
        return round(len(successful) / len(active) * 100, 1)

    @property
    def duplicates_pct(self) -> float:
        total = self.total_jobs_returned
        if not total:
            return 0.0
        return round(self.cross_provider_duplicates / total * 100, 1)

    @property
    def new_jobs_pct(self) -> float:
        total = self.total_unique_jobs
        if not total:
            return 0.0
        return round(self.new_jobs / total * 100, 1)

    def provider_contribution_pct(self, provider: str) -> float:
        total = self.total_unique_jobs
        if not total:
            return 0.0
        for s in self.provider_stats:
            if s.provider == provider:
                return round(s.unique_jobs / total * 100, 1)
        return 0.0

    def to_dict(self) -> dict:
        contrib = {
            s.provider: self.provider_contribution_pct(s.provider)
            for s in self.provider_stats
        }
        return {
            "providers": [s.to_dict() for s in self.provider_stats],
            "cross_provider_duplicates": self.cross_provider_duplicates,
            "total_unique_jobs": self.total_unique_jobs,
            "total_jobs_returned": self.total_jobs_returned,
            "new_jobs": self.new_jobs,
            "coverage_pct": self.coverage_pct,
            "duplicates_pct": self.duplicates_pct,
            "new_jobs_pct": self.new_jobs_pct,
            "provider_contribution_pct": contrib,
        }
