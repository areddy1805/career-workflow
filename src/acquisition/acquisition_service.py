"""
src/acquisition/acquisition_service.py
=======================================

Orchestrates multi-site JobSpy job fetching for one acquisition run.

This module must not import from apply_agent to avoid circular dependencies.
All terminal output and SearchPlanner usage are self-contained here.
"""

from __future__ import annotations

import logging
import time
import hashlib
from collections import defaultdict, deque
from typing import TYPE_CHECKING

from colorama import Fore, Style

if TYPE_CHECKING:
    from src.acquisition.providers.jobspy_provider import JobSpyProvider
    from src.models.models import Job

logger = logging.getLogger(__name__)

_LINE = f"{Fore.WHITE}{'─' * 68}{Style.RESET_ALL}"


def _print_section_title(text: str) -> None:
    print(f"\n{_LINE}")
    print(f"  {Fore.CYAN}{Style.BRIGHT}{text.upper()}{Style.RESET_ALL}")
    print(_LINE)


def _compute_job_hash(job: Job) -> str:
    """Compute a robust hash for cross-provider deduplication based on core attributes."""
    title = (job.title or "").lower().strip()
    company = (job.company or "").lower().strip()
    loc = (job.location or "").lower().strip()
    link = (job.apply_link or "").lower().strip()
    base_str = f"{title}::{company}::{loc}::{link}"
    return hashlib.md5(base_str.encode('utf-8')).hexdigest()


class RollingYieldTracker:
    def __init__(self, window_size: int = 25):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)
    
    def record(self, new_jobs: int, total_jobs: int):
        self.history.append((new_jobs, total_jobs))
        
    def current_yield(self) -> float:
        if not self.history:
            return 100.0
        total_new = sum(n for n, _ in self.history)
        total_all = sum(t for _, t in self.history)
        if total_all == 0:
            return 0.0
        return (total_new / total_all) * 100.0

    def has_enough_data(self) -> bool:
        return len(self.history) == self.window_size


def fetch_jobspy_jobs(
    provider: JobSpyProvider,
    search_tracks: list[dict],
) -> list:
    """
    Fetch jobs from all enabled JobSpy sites for all search queries.
    """
    if not provider.is_enabled():
        return []

    cfg = provider.config
    print("\n=== JOBSPY CONFIG ===")
    print(f"Enabled : {provider.is_enabled()}")
    print(f"Sites   : {cfg.sites}")
    print(f"Cooldown: {cfg.cooldown_seconds}")
    print("=====================\n")
    
    # Extract unique locations from the generic search tracks
    locations = list(set(q.get("location", "") for q in search_tracks if q.get("location")))
    if not locations:
        locations = ["Remote"]
        
    # Generate JobSpy-specific planned searches
    planned_queries = provider.generate_planned_searches(locations)
    
    if not planned_queries and search_tracks:
        from src.acquisition.providers.jobspy_planner import JobSpyQuery
        for site in cfg.sites:
            for q in search_tracks:
                planned_queries.append(JobSpyQuery(
                    keyword=q.get("keyword", ""),
                    location=q.get("location", ""),
                    track=q.get("track", ""),
                    provider=site,
                    search_profile=q.get("search_profile", "unknown"),
                    layer=q.get("matched_technology", "")
                ))
    
    if cfg.benchmarking_mode:
        print(f"{Fore.YELLOW}*** BENCHMARKING MODE ENABLED - LIMITING TO 10 QUERIES ***{Style.RESET_ALL}")
        planned_queries = planned_queries[:10]

    _print_section_title(
        f"fetching JobSpy jobs  "
        f"({len(planned_queries)} budgeted queries)"
    )

    seen_hashes: set[str] = set()
    all_jobs: list = []
    
    results_per_site: dict[str, int] = {site: 0 for site in cfg.sites}
    duplicates_removed: int = 0
    queries_skipped: int = 0
    queries_executed: int = 0
    
    # Adaptive Acquisition Trackers
    adaptive_cfg = getattr(cfg, "adaptive_acquisition", {})
    window_size = adaptive_cfg.get("rolling_window_size", 25)
    min_yield = adaptive_cfg.get("min_yield_percent", 3.0)
    
    provider_trackers = {site: RollingYieldTracker(window_size) for site in cfg.sites}
    stopped_providers = set()
    
    # Analytics
    query_analytics = []

    for i, query in enumerate(planned_queries, 1):
        site = query.provider
        keyword = query.keyword
        location = query.location
        
        if site in stopped_providers:
            queries_skipped += 1
            continue

        if not provider.is_site_available(site):
            print(f"  {Fore.YELLOW}[JOBSPY:{site.upper()}]{Style.RESET_ALL} On cooldown — skipping.")
            queries_skipped += 1
            continue

        queries_executed += 1
        t_start = time.perf_counter()

        try:
            print(f"\nCalling JobSpy: {site} | {keyword} | {location}")
            jobs = provider.search(keyword=keyword, location=location, site=site)
            # Display top 3
            for job in jobs[:3]:
                print(f"  -> {job.title} | {job.company} | {job.location}")
        except Exception as exc:
            print(f"  {Fore.RED}[JOBSPY:{site.upper()}]{Style.RESET_ALL} {keyword!r} @ {location!r}  →  {exc}")
            continue

        latency = time.perf_counter() - t_start
        
        new_jobs = []
        for job in jobs:
            job_hash = _compute_job_hash(job)
            if job_hash in seen_hashes:
                print(f"Duplicate skipped: {job.title} at {job.company}")
                duplicates_removed += 1
                continue
            
            seen_hashes.add(job_hash)
            results_per_site[site] += 1
            
            setattr(job, "acquisition_source", "live")
            setattr(job, "search_track", query.track)
            setattr(job, "search_query", keyword)
            setattr(job, "search_profile", query.search_profile)
            setattr(job, "matched_technology", query.layer)
            new_jobs.append(job)

        all_jobs.extend(new_jobs)
        
        # Track Yield
        total_fetched = len(jobs)
        new_count = len(new_jobs)
        provider_trackers[site].record(new_count, total_fetched)
        
        query_analytics.append({
            "query": keyword,
            "provider": site,
            "jobs_found": total_fetched,
            "new_jobs": new_count,
            "runtime": latency
        })

        print(
            f"  {Fore.CYAN}[{site.upper():<8}]{Style.RESET_ALL}  "
            f"{keyword[:30]:<30}  "
            f"{Fore.GREEN}{new_count:>3} new{Style.RESET_ALL}  "
            f"({len(all_jobs)} total)"
        )
        
        # Check adaptive stopping
        tracker = provider_trackers[site]
        if tracker.has_enough_data():
            current_yield = tracker.current_yield()
            if current_yield < min_yield:
                print(f"  {Fore.RED}[ADAPTIVE STOP]{Style.RESET_ALL} {site.upper()} rolling yield is {current_yield:.1f}% (<{min_yield}%). Stopping provider.")
                stopped_providers.add(site)

        if cfg.cooldown_seconds > 0:
            time.sleep(cfg.cooldown_seconds)

    print(f"\n  {Fore.CYAN}JobSpy total unique jobs: {Style.BRIGHT}{len(all_jobs)}{Style.RESET_ALL}")
    
    # Compute Analytics Summary
    total_planned = len(planned_queries)
    failures = sum(h.get("failed_searches", 0) for h in provider.health_summary().values())
    
    print("\n" + "=" * 57)
    print("JOBSPY SUMMARY")
    print("=" * 57)
    print("Provider          JobSpy")
    print("Sites")
    for site in cfg.sites:
        status = "stopped" if site in stopped_providers else ("cooldown" if not provider.is_site_available(site) else "active")
        print(f"  {site.capitalize():<14} ({status})")

    print(f"Queries Planned   {total_planned}")
    print(f"Queries Executed  {queries_executed}")
    print(f"Queries Skipped   {queries_skipped}")
    
    print("Results by Site")
    for site in cfg.sites:
        print(f"  {site.capitalize():<14} {results_per_site[site]}")

    print(f"Duplicates        {duplicates_removed}")
    print(f"Failures          {failures}")
    print(f"Final Jobs        {len(all_jobs)}")
    
    if queries_executed > 0:
        total_time = sum(a["runtime"] for a in query_analytics)
        overall_yield = (len(all_jobs) / sum(a["jobs_found"] for a in query_analytics)) * 100 if sum(a["jobs_found"] for a in query_analytics) > 0 else 0
        print(f"Overall Yield     {overall_yield:.1f}%")
        print(f"Average Runtime   {total_time/queries_executed:.2f}s per search")
        
        # Top 3 Queries
        sorted_analytics = sorted(query_analytics, key=lambda x: x["new_jobs"], reverse=True)
        print("Top 3 Queries (by new jobs):")
        for a in sorted_analytics[:3]:
            if a["new_jobs"] > 0:
                print(f"  {a['query'][:20]:<20} | {a['provider']:<8} | {a['new_jobs']} new")
                
    else:
        print(f"Skipped reason    No valid sites or keywords configured")

    print("=" * 57)

    return all_jobs
