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

from colorama import Fore, Style

from src.acquisition.providers.jobspy_provider import JobSpyProvider
from src.search.planner import SearchPlanner

logger = logging.getLogger(__name__)

# Matches the LINE constant used throughout apply_agent's display helpers.
_LINE = f"{Fore.WHITE}{'─' * 68}{Style.RESET_ALL}"


def _print_section_title(text: str) -> None:
    """Print a bold titled section divider — identical output to apply_agent's helper."""
    print(f"\n{_LINE}")
    print(f"  {Fore.CYAN}{Style.BRIGHT}{text.upper()}{Style.RESET_ALL}")
    print(_LINE)


def fetch_jobspy_jobs(
    provider: JobSpyProvider,
    search_tracks: list[dict],
) -> list:
    """
    Fetch jobs from all enabled JobSpy sites for all search queries.

    Failure isolation:
        - A challenge on site X puts X on cooldown; Y and Z continue.
        - A network error on one query is logged and skipped; the loop continues.
        - A parse error on one row is logged and skipped; other rows continue.

    Returns a flat list of Job objects deduplicated by job_id within this
    function (cross-provider dedup happens later in merge_jobs).

    This function MUST NOT modify any job objects from the Naukri path.
    """
    if not provider.is_enabled():
        return []

    cfg = provider.config
    print("\n=== JOBSPY CONFIG ===")
    print(f"Enabled : {provider.is_enabled()}")
    print(f"Sites   : {cfg.sites}")
    print(f"Cooldown: {cfg.cooldown_seconds}")
    print("=====================\n")
    seen_ids: set[str] = set()
    all_jobs: list = []
    total_queries = len(search_tracks) * len(cfg.sites)
    done = 0

    _print_section_title(
        f"fetching JobSpy jobs  "
        f"({len(search_tracks)} queries × {len(cfg.sites)} sites)"
    )

    print(f"Search tracks: {len(search_tracks)}")
    for i, q in enumerate(search_tracks, 1):
        print(f"{i}. keyword='{q.get('keyword')}' " f"location='{q.get('location')}'")

    for site in cfg.sites:
        if not provider.is_site_available(site):
            print(
                f"  {Fore.YELLOW}[JOBSPY:{site.upper()}]{Style.RESET_ALL}  "
                f"On cooldown — skipping."
            )
            continue

        for query in search_tracks:
            keyword = query.get("keyword", "")
            location = query.get("location", "")
            done += 1

            try:
                print(
                    f"\nCalling JobSpy:"
                    f"\n  Site     : {site}"
                    f"\n  Keyword  : {keyword}"
                    f"\n  Location : {location}"
                )
                jobs = provider.search(
                    keyword=keyword,
                    location=location,
                    site=site,
                )
                for job in jobs[:3]:
                    print(f"  -> {job.title} | " f"{job.company} | " f"{job.location}")
            except Exception as exc:
                # Failure isolation: log and continue.  The exception type
                # (challenge vs network vs parse) was already handled inside
                # provider.search(); we just skip this query.
                print(
                    f"  {Fore.RED}[JOBSPY:{site.upper()}]{Style.RESET_ALL}  "
                    f"{keyword!r} @ {location!r}  →  {exc}"
                )
                continue

            new_jobs = []
            for job in jobs:
                if job.job_id in seen_ids:
                    print(f"Duplicate skipped: {job.job_id}")
                    continue
                seen_ids.add(job.job_id)
                # Tag the acquisition metadata used by print_acquisition_summary
                setattr(job, "acquisition_source", "live")
                setattr(job, "search_track", query.get("track", ""))
                setattr(job, "search_query", keyword)
                setattr(job, "search_profile", query.get("search_profile", "unknown"))
                setattr(job, "matched_technology", query.get("matched_technology", ""))
                new_jobs.append(job)

            all_jobs.extend(new_jobs)

            print(
                f"  {Fore.CYAN}[{site.upper():<8}]{Style.RESET_ALL}  "
                f"{keyword[:30]:<30}  "
                f"{Fore.GREEN}{len(new_jobs):>3} new{Style.RESET_ALL}  "
                f"({len(all_jobs)} total)"
            )

            # Polite cooldown between queries to reduce ban risk
            if cfg.cooldown_seconds > 0:
                time.sleep(cfg.cooldown_seconds)

    print(
        f"\n  {Fore.CYAN}"
        f"JobSpy total unique jobs: "
        f"{Style.BRIGHT}{len(all_jobs)}{Style.RESET_ALL}"
    )

    print("\n========== JOBSPY SUMMARY ==========")
    print(f"Queries      : {len(search_tracks)}")
    print(f"Sites        : {len(cfg.sites)}")
    print(f"API Calls    : {total_queries}")
    print(f"Unique Jobs  : {len(all_jobs)}")
    print("====================================")

    return all_jobs
