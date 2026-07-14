import asyncio
import logging
from pprint import pprint

from src.acquisition.registry import ProviderRegistry
from src.search.planner import SearchPlanner
from src.acquisition.manager import AcquisitionManager
from src.acquisition.models import SearchPlan

logging.basicConfig(level=logging.INFO)

async def test_run():
    registry = ProviderRegistry()
    print("--- Provider Registry Info ---")
    info = registry.provider_info()
    for p in info:
        print(f"{p['name']} ({p.get('lifecycle_state', 'production')}): enabled={p['enabled']}, priority={p['priority']}")

    print("\n--- Generating Search Plans ---")
    planner = SearchPlanner()
    plans = planner.generate_plans()
    
    # We will test live acquisition on a couple of top priority plans for speed.
    test_plans = plans[:2]
    print(f"Executing acquisition on {len(test_plans)} test plans...")
    for p in test_plans:
        print(f"Plan: {p.generated_query} [{p.priority}]")

    manager = AcquisitionManager(registry)
    results, summary = manager.acquire(test_plans)
    
    print("\n--- Live Acquisition Results ---")
    print(f"Total deduplicated jobs found: {len(results)}")
    for j in results[:5]:
        print(f"\nJob: {j.title} @ {j.company}")
        print(f"  Canonical Provider: {getattr(j, 'provider', 'unknown')}")
        print(f"  Provenance - Query: {getattr(j, 'search_query', 'N/A')}")
        print(f"  Provenance - Tech: {getattr(j, 'matched_technology', 'N/A')}")
        print(f"  Also seen on: {getattr(j, 'also_seen_on', [])}")

if __name__ == "__main__":
    asyncio.run(test_run())
