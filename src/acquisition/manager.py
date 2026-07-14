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
        caps_map = self._registry.native_apply_map()

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

            if hasattr(provider, "reset_metrics"):
                provider.reset_metrics()

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

            if hasattr(provider, "get_metrics"):
                pm = provider.get_metrics()
                stats.http_requests = pm.get("http_requests", 0)
                stats.http_success = pm.get("http_success", 0)
                stats.parse_success = pm.get("parse_success", 0)
                stats.jobs_parsed = pm.get("jobs_parsed", 0)
                stats.jobs_normalized = pm.get("jobs_normalized", 0)
                # jobs_returned is already accumulated per-plan in the loop,
                # but we can sync it with provider metrics if preferred.

            provider_stats.append(stats)
            all_normalized.extend(provider_jobs)

        # Cross-provider deduplication
        total_before_dedup = len(all_normalized)
        unique_normalized, cross_duplicates, dedup_analysis = self._deduplicator.deduplicate(all_normalized)

        logger.info(
            "Acquisition complete: %d total -> %d unique (%d cross-provider duplicates)",
            total_before_dedup, len(unique_normalized), cross_duplicates,
        )
        
        if self._artifact_dir:
            try:
                self._artifact_dir.mkdir(parents=True, exist_ok=True)
                path = self._artifact_dir / "duplicate_analysis.json"
                tmp = path.with_suffix(".tmp")
                import json
                tmp.write_text(
                    json.dumps(dedup_analysis, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                tmp.replace(path)
            except Exception as e:
                logger.warning("Failed to write duplicate_analysis.json: %s", e)

        # Compute planner stats
        planner_stats = {
            "generated_queries": len(plans),
            "providers_active": len(providers),
            "queries_per_provider": {
                p.PROVIDER_NAME: len(self._filter_plans(plans, p.PROVIDER_NAME))
                for p in providers
            }
        }

        # Build summary
        summary = AcquisitionSummary(
            provider_stats=provider_stats,
            cross_provider_duplicates=cross_duplicates,
            total_unique_jobs=len(unique_normalized),
            total_jobs_returned=total_before_dedup,
            planner_stats=planner_stats,
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
        
        Dynamically deduplicates plans based on provider capabilities to prevent
        Cartesian explosion. For example, if a provider doesn't support 'experience',
        we collapse all plans that only differ by experience into a single plan.
        """
        # First filter to valid plans for this provider
        valid = [
            p for p in plans
            if not p.target_providers or provider_name in p.target_providers
        ]
        
        provider = self._registry.get_provider(provider_name)
        if not provider:
            return valid
            
        caps = provider.capabilities()
        deduped = []
        seen = set()
        
        for p in valid:
            # If the provider ignores a dimension, force its value to a constant in the dedup key
            # so that plans differing ONLY in that dimension are collapsed.
            exp_key = p.experience if caps.supports_experience_filter else 0
            loc_key = p.location if caps.supports_location_filter else ""
            
            key = (p.generated_query, loc_key, exp_key)
            if key not in seen:
                seen.add(key)
                deduped.append(p)
                
        return deduped

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

        # Update rolling health history
        try:
            history_path = Path("data/provider_health_history.json")
            history = {}
            if history_path.exists():
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)

            for stat in summary.provider_stats:
                provider = stat.provider
                if provider not in history:
                    history[provider] = []
                
                entry = {
                    "run_id": run_id,
                    "date": datetime.now(timezone.utc).isoformat(),
                    "success_pct": stat.success_pct,
                    "failure_pct": stat.failure_pct,
                    "latency_ms": round(stat.latency_ms, 1),
                    "last_successful_search": stat.last_successful_search,
                    "last_failure": stat.last_failure,
                    "last_challenge": stat.last_challenge,
                    "searches_executed": stat.searches_executed,
                    "jobs_returned": stat.jobs_returned,
                    "unique_jobs": stat.unique_jobs,
                    "http_requests": stat.http_requests,
                    "http_success": stat.http_success,
                    "parse_success": stat.parse_success,
                    "jobs_parsed": stat.jobs_parsed,
                    "jobs_normalized": stat.jobs_normalized,
                }
                
                # Prepend new entry
                history[provider].insert(0, entry)
                # Keep last 20 executions
                history[provider] = history[provider][:20]

            tmp_hist = history_path.with_suffix(".tmp")
            with open(tmp_hist, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            tmp_hist.replace(history_path)
            logger.debug("Updated provider health history in %s", history_path)
        except Exception as exc:
            logger.warning("Failed to update provider health history: %s", exc)
