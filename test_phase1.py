from src.acquisition.registry import ProviderRegistry
from src.acquisition.manager import AcquisitionManager
from src.acquisition.provider import _ProviderRegistry
from src.search.planner import SearchPlanner
import json
import logging

logging.basicConfig(level=logging.INFO)

print("--- PHASE 1: Architecture Audit ---")

registry = ProviderRegistry()

print("\n1. Auto-registration & Discovery:")
registered = _ProviderRegistry.all_names()
print(f"Registered Providers: {registered}")
expected = {'naukri', 'remoteok', 'weworkremotely', 'google_jobs', 'wellfound', 'instahyre', 'foundit'}
missing = expected - set(registered)
if missing:
    print(f"FAIL: Missing providers from registration: {missing}")
else:
    print("PASS: All expected providers auto-registered.")

infos = registry.provider_info()
print(f"Provider Infos: {[p['name'] for p in infos]}")

print("\n2. Capabilities & Configurations:")
for info in infos:
    print(f"  - {info['name']}: Enabled={info['enabled']}, Type={info['provider_type']}, Caps={info['capabilities']}")

print("\n3. Search Planner Integration:")
planner = SearchPlanner()
plans = planner.generate_plans()
print(f"Generated {len(plans)} SearchPlans.")
if plans:
    print(f"Sample Plan: {plans[0]}")

print("\n4. AcquisitionManager Initialization:")
manager = AcquisitionManager(registry=registry, artifact_dir="data/runs/audit_test")
print(f"AcquisitionManager initialized. Deduplicator: {manager._deduplicator}")
print(f"Manager has {len(registry.enabled_providers())} enabled providers.")

print("-----------------------------------")
