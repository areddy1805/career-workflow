import sys
import logging
from dotenv import load_dotenv
load_dotenv()
from src.acquisition.registry import ProviderRegistry
from src.acquisition.models import SearchPlan, ProviderPriority, ProviderHealthStatus
from src.search.planner import SearchPlanner
import json

logging.basicConfig(level=logging.INFO)
provider_name = sys.argv[1]

print(f"\n--- Testing Provider: {provider_name} ---")

class MockRegistry(ProviderRegistry):
    def _resolve_enabled_providers(self):
        return [provider_name]
    
    def _discover_configs(self):
        configs = super()._discover_configs()
        if provider_name in configs:
            configs[provider_name]["enabled"] = True
        return configs

registry = MockRegistry()
provider = registry.get_provider(provider_name)

if not provider:
    print(f"FAIL: Could not load provider '{provider_name}'")
    sys.exit(1)

print(f"1. Initialized successfully.")

try:
    health = provider.health()
    print(f"2. Health Check: {health.status.value}")
except Exception as e:
    print(f"FAIL: Health check raised exception: {e}")
    sys.exit(1)

print("3. Executing live search...")
planner = SearchPlanner()
plans = planner.generate_plans()
plan = plans[0] if plans else SearchPlan(
    profile="test", generated_query="software engineer", location="Pune",
    target_providers=[provider_name], priority=ProviderPriority.NORMAL
)
plan.generated_query = "python backend developer"

try:
    jobs = provider.search(plan)
    print(f"Returned {len(jobs)} jobs.")
    if jobs:
        j = jobs[0]
        print("\nFirst Job Verification:")
        print(f"  ID: {j.provider_job_id}")
        print(f"  Title: {j.title}")
        print(f"  Company: {j.company}")
        print(f"  URL: {j.application_url or j.provider_url}")
        print(f"  Provenance Query: {j.provenance.generated_query}")
        
        if not j.provider_job_id or not j.title or not j.company:
            print("FAIL: Missing core normalized fields (ID, title, company)")
        else:
            print("PASS: Core normalization valid")
    else:
        print("WARNING: No jobs returned.")
except Exception as e:
    print(f"FAIL: Search raised exception: {e}")

print("------------------------------------------")
