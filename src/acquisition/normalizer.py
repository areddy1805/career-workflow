"""
src/acquisition/normalizer.py — Bridge from NormalizedJob to the existing Job model.

This is the ONLY place in the codebase that knows about both worlds.
Everything above returns NormalizedJob. Everything below consumes Job.
"""
from __future__ import annotations

import logging
from typing import Any

from src.acquisition.models import NormalizedJob
from src.models.models import Job

logger = logging.getLogger(__name__)


class JobNormalizer:
    """
    Converts NormalizedJob → Job (src/models/models.py).

    The existing pipeline (classify, select, apply) is entirely unchanged.
    This class is the anti-corruption layer at the acquisition boundary.
    """

    @staticmethod
    def normalized_to_job(nj: NormalizedJob, *, supports_auto_apply: bool = False) -> Job:
        """
        Map a NormalizedJob to the legacy Job model used by the pipeline.

        Fields that have no equivalent in Job are preserved as dynamic
        attributes via setattr — exactly as the existing acquisition code does.
        This ensures backward compatibility with the entire downstream pipeline.
        """
        # Build the core Job
        job = Job(
            job_id=str(nj.provider_job_id),
            title=nj.title,
            company=nj.company,
            location=nj.location,
            experience=nj.experience,
            salary=nj.salary,
            posted_date=nj.posted_date,
            apply_link=nj.application_url,
            description=nj.description,
            tags=list(nj.skills or []),
        )

        # Acquisition provenance — carried as dynamic attributes (same as before)
        job.provenance = nj.provenance.to_dict()
        setattr(job, "acquisition_source", "live")
        setattr(job, "search_track", nj.provenance.track or "TIER_B")
        setattr(job, "search_query", nj.provenance.generated_query)
        setattr(job, "search_profile", nj.provenance.search_profile)
        setattr(job, "matched_technology", nj.provenance.matched_technology)

        # Provider identity — new fields, preserved as dynamic attributes
        setattr(job, "provider", nj.provider)
        setattr(job, "provider_name", nj.provider_name)
        setattr(job, "provider_job_id", nj.provider_job_id)
        setattr(job, "provider_url", nj.provider_url)
        setattr(job, "application_url", nj.application_url)
        setattr(job, "job_board", nj.job_board)
        setattr(job, "technology_group", nj.provenance.technology_group)
        setattr(job, "also_seen_on", nj.provenance.also_seen_on)

        # Application routing — the key flag read by run_application_batch
        # Non-Naukri providers (supports_auto_apply=False) automatically
        # route to External Apply queue without any pipeline changes.
        setattr(job, "is_external_apply", not supports_auto_apply)

        # Queue enrichment fields
        setattr(job, "original_job_url", nj.provider_url)
        setattr(job, "apply_source", nj.provider_name)

        # Work mode (used by location_work_mode_gate)
        setattr(job, "work_mode", nj.remote_type or "")
        setattr(job, "employment_type", nj.employment_type or "")

        # Extended provider metadata (preserved for queue display)
        setattr(job, "provider_metadata", nj.provider_metadata)

        return job

    @staticmethod
    def batch(
        normalized_jobs: list[NormalizedJob],
        capabilities_map: dict[str, bool],
    ) -> list[Job]:
        """
        Convert a list of NormalizedJobs to Jobs.

        capabilities_map: {provider_name: supports_auto_apply}
        """
        result = []
        for nj in normalized_jobs:
            supports_auto = capabilities_map.get(nj.provider, False)
            try:
                job = JobNormalizer.normalized_to_job(nj, supports_auto_apply=supports_auto)
                result.append(job)
            except Exception as exc:
                logger.warning(
                    "Failed to normalize job: provider=%s job_id=%s error=%s",
                    nj.provider, nj.provider_job_id, exc,
                )
        return result
