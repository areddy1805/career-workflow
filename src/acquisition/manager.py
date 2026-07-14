"""
src/acquisition/manager.py — Acquisition orchestration across all providers.

AcquisitionManager is the single entry point for the pipeline's acquire() stage.
It knows nothing about individual providers — it delegates everything to them.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.acquisition.deduplicator import CrossProviderDeduplicator
from src.acquisition.models import (
    AcquisitionSummary,
    NormalizedJob,
    ProviderRunStats,
    SearchPlan,
)
from src.acquisition.normalizer import JobNormalizer
from src.acquisition.registry import ProviderRegistry

logger = logging.getLogger(__name__)


class AcquisitionManager:
    """
    Orchestrates job acquisition across all enabled providers.

    Responsibilities:
      1. Iterate enabled providers
      2. For each provider, iterate applicable SearchPlans
      3. Collect NormalizedJobs
      4. Run cross-provider deduplication (with metadata merge)
      5. Return (list[Job], AcquisitionSummary)
      6. Write provider_summary.json artifact

    The pipeline asks for Jobs. It never knows how many providers ran.
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        deduplicator: CrossProviderDeduplicator | None = None,
        artifact_dir: str | Path | None = None,
    ) -> None:
        self._registry = registry
        self._deduplicator = deduplicator or CrossProviderDeduplicator()
        self._artifact_dir = Path(artifact_dir) if artifact_dir else None

    def acquire(
        self,
        plans: list[SearchPlan],
        *,
        run_id: str = "",
    ):
        """
        Run acquisition across all providers.

        Returns:
            (jobs: list[Job], summary: AcquisitionSummary)

        Jobs are the legacy Job objects expected by the downstream pipeline.
        """
        providers = self._registry.enabled_providers()
        caps_map = self._registry.supports_auto_apply_map()

        if not providers:
            logger.warning("No providers enabled — acquisition returning 0 jobs")
            summary = AcquisitionSummary()
            return [], summary

        all_normalized: list[NormalizedJob] = []
        provider_stats: list[ProviderRunStats] = []

        for provider in providers:
            caps = provider.capabilities()
            applicable_plans = self._filter_plans(plans, provider.PROVIDER_NAME)

            if not applicable_plans:
                logger.debug(
                    "Provider '%s' has no applicable plans — skipping",
                    provider.PROVIDER_NAME,
                )
                continue

            stats = ProviderRunStats(
                provider=provider.PROVIDER_NAME,
                provider_type=provider.PROVIDER_TYPE.value,
            )

            provider_jobs: list[NormalizedJob] = []
            t0 = time.perf_counter()

            for plan in applicable_plans:
                stats.searches_executed += 1
                try:
                    fetched = provider.search(plan)
                    stats.jobs_returned += len(fetched)
                    provider_jobs.extend(fetched)
                    if fetched:
                        stats.last_successful_search = datetime.now(timezone.utc).isoformat()
                    logger.debug(
                        "Provider %s search '%s' returned %d jobs",
                        provider.PROVIDER_NAME, plan.generated_query, len(fetched),
                    )
                except Exception as exc:
                    stats.failures += 1
                    stats.last_failure = datetime.now(timezone.utc).isoformat()
                    logger.warning(
                        "Provider '%s' search failed: plan='%s' error=%s",
                        provider.PROVIDER_NAME, plan.generated_query, exc,
                    )

            stats.latency_ms = (time.perf_counter() - t0) * 1000
            stats.unique_jobs = len(provider_jobs)  # before cross-provider dedup
            provider_stats.append(stats)
            all_normalized.extend(provider_jobs)

        # Cross-provider deduplication
        total_before_dedup = len(all_normalized)
        unique_normalized, cross_duplicates = self._deduplicator.deduplicate(all_normalized)

        logger.info(
            "Acquisition complete: %d total → %d unique (%d cross-provider duplicates)",
            total_before_dedup, len(unique_normalized), cross_duplicates,
        )

        # Build summary
        summary = AcquisitionSummary(
            provider_stats=provider_stats,
            cross_provider_duplicates=cross_duplicates,
            total_unique_jobs=len(unique_normalized),
            total_jobs_returned=total_before_dedup,
        )

        # Write observability artifact
        if self._artifact_dir:
            self._write_provider_summary(summary, run_id)

        # Convert to legacy Job objects
        jobs = JobNormalizer.batch(unique_normalized, caps_map)

        return jobs, summary

    def _filter_plans(
        self, plans: list[SearchPlan], provider_name: str
    ) -> list[SearchPlan]:
        """
        Return plans applicable to this provider.

        If a plan has target_providers = [] it applies to all.
        If it lists specific providers, only those get the plan.
        """
        return [
            p for p in plans
            if not p.target_providers or provider_name in p.target_providers
        ]

    def _write_provider_summary(self, summary: AcquisitionSummary, run_id: str) -> None:
        """Write provider_summary.json to the artifact directory."""
        try:
            self._artifact_dir.mkdir(parents=True, exist_ok=True)
            path = self._artifact_dir / "provider_summary.json"
            tmp = path.with_suffix(".tmp")
            payload = {
                "schema_version": 1,
                "run_id": run_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "data": summary.to_dict(),
            }
            tmp.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
            tmp.replace(path)
            logger.debug("Wrote provider_summary.json to %s", path)
        except Exception as exc:
            logger.warning("Failed to write provider_summary.json: %s", exc)
