"""
src/acquisition/deduplicator.py — Cross-provider deduplication with metadata merge.

Deduplication strategy (priority order):
  1. Exact application_url match
  2. Exact provider_job_id within same job_board
  3. company + title + location fingerprint (normalized)
  4. Description Jaccard similarity (threshold configurable, default 0.85)

Merge strategy: first-seen provider wins on core fields,
but provider_metadata is MERGED from all providers.
This preserves information — we never throw away provider-specific data.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from src.acquisition.models import NormalizedJob

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Lowercase, strip punctuation and extra whitespace for comparison."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _fingerprint(job: NormalizedJob) -> str:
    """company + title + location fingerprint for fast dedup."""
    parts = [
        _normalize_text(job.company),
        _normalize_text(job.title),
        _normalize_text(job.location),
    ]
    return "||".join(parts)


def _jaccard(a: str, b: str) -> float:
    """Word-level Jaccard similarity between two strings."""
    if not a or not b:
        return 0.0
    set_a = set(_normalize_text(a).split())
    set_b = set(_normalize_text(b).split())
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union


def _merge_metadata(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    """
    Merge two provider_metadata dicts.

    Keys from 'extra' are added only if not already present in 'base'.
    The 'sources' list is accumulated to preserve all provider origins.
    """
    merged = dict(base)
    for k, v in extra.items():
        if k not in merged:
            merged[k] = v
    return merged


def _merge_jobs(winner: NormalizedJob, duplicate: NormalizedJob) -> NormalizedJob:
    """
    Merge a duplicate into the winner job.

    - Core fields: winner always wins (first seen)
    - provider_metadata: merged from both
    - provenance.also_seen_on: accumulates all extra providers
    - skills/technologies: union
    """
    # Merge metadata
    merged_meta = _merge_metadata(winner.provider_metadata, duplicate.provider_metadata)

    # Note the duplicate's provider in provenance
    also_seen = list(winner.provenance.also_seen_on)
    if duplicate.provider not in also_seen and duplicate.provider != winner.provider:
        also_seen.append(duplicate.provider)

    # Enrich skills and technologies
    merged_skills = list(dict.fromkeys(winner.skills + duplicate.skills))
    merged_tech = list(dict.fromkeys(winner.technologies + duplicate.technologies))

    # Prefer richer description
    description = winner.description
    if not description and duplicate.description:
        description = duplicate.description
    elif duplicate.description and len(duplicate.description) > len(description) * 1.5:
        # If duplicate has substantially more content, merge it in
        description = winner.description + "\n\n[Additional source]\n" + duplicate.description

    # Prefer populated optional fields from duplicate if winner is missing them
    salary = winner.salary or duplicate.salary
    experience = winner.experience or duplicate.experience
    employment_type = winner.employment_type or duplicate.employment_type
    remote_type = winner.remote_type or duplicate.remote_type
    posted_date = winner.posted_date or duplicate.posted_date

    # Build merged job (dataclasses are immutable-ish; create new one)
    from dataclasses import replace
    winner.provenance.also_seen_on = also_seen
    merged = replace(
        winner,
        description=description,
        skills=merged_skills,
        technologies=merged_tech,
        salary=salary,
        experience=experience,
        employment_type=employment_type,
        remote_type=remote_type,
        posted_date=posted_date,
        provider_metadata=merged_meta,
    )
    return merged


class CrossProviderDeduplicator:
    """
    Deduplicates NormalizedJob lists across multiple providers.

    Preserves information by merging metadata from all matching sources
    rather than simply discarding duplicates.
    """

    def __init__(self, jaccard_threshold: float = 0.85) -> None:
        self.jaccard_threshold = jaccard_threshold

    def deduplicate(
        self, jobs: list[NormalizedJob]
    ) -> tuple[list[NormalizedJob], int]:
        """
        Returns (deduplicated_jobs, duplicates_removed_count).

        Processes jobs in order — first encountered wins on core fields,
        but metadata from all duplicates is merged in.
        """
        unique: list[NormalizedJob] = []
        duplicates_removed = 0

        # Index structures for O(1) lookups on the common cases
        by_application_url: dict[str, int] = {}    # url -> index in unique
        by_board_job_id: dict[str, int] = {}        # "board::id" -> index
        by_fingerprint: dict[str, int] = {}         # fingerprint -> index

        for job in jobs:
            winner_idx = self._find_duplicate(
                job, by_application_url, by_board_job_id, by_fingerprint, unique
            )

            if winner_idx is not None:
                # Merge this job's metadata into the winner
                unique[winner_idx] = _merge_jobs(unique[winner_idx], job)
                duplicates_removed += 1
                logger.debug(
                    "Deduped: %s @ %s (provider=%s) -> winner provider=%s",
                    job.title, job.company, job.provider,
                    unique[winner_idx].provider,
                )
            else:
                # New unique job
                idx = len(unique)
                unique.append(job)

                # Index it
                if job.application_url:
                    by_application_url[job.application_url] = idx
                board_key = f"{job.job_board}::{job.provider_job_id}"
                if job.provider_job_id:
                    by_board_job_id[board_key] = idx
                fp = _fingerprint(job)
                if fp:
                    by_fingerprint[fp] = idx

        logger.info(
            "Deduplication: %d in → %d unique, %d removed",
            len(jobs), len(unique), duplicates_removed,
        )
        return unique, duplicates_removed

    def _find_duplicate(
        self,
        job: NormalizedJob,
        by_url: dict[str, int],
        by_board_id: dict[str, int],
        by_fp: dict[str, int],
        unique: list[NormalizedJob],
    ) -> int | None:
        """Return index of existing duplicate, or None if job is truly new."""
        # 1. Exact application URL
        if job.application_url and job.application_url in by_url:
            return by_url[job.application_url]

        # 2. Same board + same job ID
        board_key = f"{job.job_board}::{job.provider_job_id}"
        if job.provider_job_id and board_key in by_board_id:
            return by_board_id[board_key]

        # 3. Fingerprint match
        fp = _fingerprint(job)
        if fp and fp in by_fp:
            return by_fp[fp]

        # 4. Description similarity (only when fingerprint matches partially)
        # Limit to candidates with same company to keep this fast
        if job.description:
            company_norm = _normalize_text(job.company)
            for idx, candidate in enumerate(unique):
                if _normalize_text(candidate.company) != company_norm:
                    continue
                if not candidate.description:
                    continue
                sim = _jaccard(job.description[:500], candidate.description[:500])
                if sim >= self.jaccard_threshold:
                    return idx

        return None
