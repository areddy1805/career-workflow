import sys
import logging
from dotenv import load_dotenv
load_dotenv()
from src.acquisition.manager import AcquisitionManager
from src.acquisition.registry import ProviderRegistry
from src.search.planner import SearchPlanner

logging.basicConfig(level=logging.INFO)

print("--- PHASE 3: Live Acquisition ---")

registry = ProviderRegistry()
for name, config in registry._provider_configs.items():
    config["enabled"] = True

registry._load() # Reload to apply the forced enable

print(f"Loaded {len(registry.enabled_providers())} providers.")

manager = AcquisitionManager(registry=registry, artifact_dir="data/runs/audit")
planner = SearchPlanner()
plans = planner.generate_plans()

# Limit plans to 1 for quick test
print(f"Running acquisition for 1 plan out of {len(plans)}...")
# use acquire() instead of run_acquisition_cycle
jobs, summary = manager.acquire(plans[:1], run_id="audit_run_123")

print("\n--- Summary ---")
# manager.acquire returns (jobs, AcquisitionSummary)
print(f"Total Unique Jobs: {summary.total_unique_jobs}")
print(f"Total Jobs Returned (before dedup): {summary.total_jobs_returned}")
print(f"Cross-provider Duplicates: {summary.cross_provider_duplicates}")

for stats in summary.provider_stats:
    print(f"  {stats.provider}: {stats.jobs_returned} returned, {stats.unique_jobs} unique, {stats.failures} failures")

