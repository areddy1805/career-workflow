import json
from collections import defaultdict
from typing import Any, List
from pathlib import Path

class AnalyticsEngine:
    def __init__(self, run_id: str, acquired_jobs: List[Any], rejected_jobs: List[Any], ledger: Any = None):
        self.run_id = run_id
        
        # Convert all jobs to dicts for easy access
        self.jobs = []
        for j in acquired_jobs:
            if hasattr(j, "__dict__"):
                self.jobs.append(j.__dict__)
            else:
                self.jobs.append(j)
                
        self.ledger = ledger

    def generate_query_analytics(self) -> list[dict[str, Any]]:
        # query -> provider -> stats
        queries = defaultdict(lambda: {
            "jobs_returned": 0,
            "jobs_normalized": 0,
            "duplicates": 0,
            "qualified": 0,
            "selected": 0,
            "applications": 0,
            "provider": ""
        })
        
        for j in self.jobs:
            prov = j.get("provenance", {})
            q = prov.get("generated_query", "unknown")
            provider = prov.get("provider", "unknown")
            
            key = f"{provider}::{q}"
            queries[key]["provider"] = provider
            queries[key]["query"] = q
            queries[key]["jobs_returned"] += 1
            
            # Count deduplication (if it has also_seen_on it's a cross-provider dedup anchor,
            # but wait, duplicates are dropped! We need to know total returned vs normalized.
            # Actually, `self.jobs` only has unique normalized jobs.
            # To get raw jobs, we'd need them before dedup. 
            # For now we count what reached classification.
            queries[key]["jobs_normalized"] += 1
            
            history = j.get("decision_history", [])
            stages = [h.get("stage") for h in history]
            
            if "Selection" not in stages and not j.get("rejection_record"):
                # If no rejection record at classification, it's qualified
                queries[key]["qualified"] += 1
                
            if not j.get("rejection_record"):
                queries[key]["selected"] += 1
                
        return list(queries.values())

    def generate_profile_analytics(self) -> list[dict[str, Any]]:
        profiles = defaultdict(lambda: {
            "search_profile": "",
            "jobs": 0,
            "selected": 0,
            "applied": 0
        })
        
        for j in self.jobs:
            prov = j.get("provenance", {})
            profile = prov.get("search_profile", "unknown")
            
            profiles[profile]["search_profile"] = profile
            profiles[profile]["jobs"] += 1
            
            if not j.get("rejection_record"):
                profiles[profile]["selected"] += 1
                
        # Calculate yield
        results = []
        for p in profiles.values():
            p["yield_pct"] = round(p["selected"] / p["jobs"] * 100, 1) if p["jobs"] > 0 else 0
            results.append(p)
            
        # Rank by yield
        results.sort(key=lambda x: x["yield_pct"], reverse=True)
        return results

    def generate_provider_quality(self) -> list[dict[str, Any]]:
        providers = defaultdict(lambda: {
            "provider": "",
            "jobs_discovered": 0,
            "qualified_jobs": 0,
            "selected_jobs": 0,
            "applications": 0,
            "yield_pct": 0.0
        })
        
        for j in self.jobs:
            prov = j.get("provenance", {})
            p = prov.get("provider", "unknown")
            
            providers[p]["provider"] = p
            providers[p]["jobs_discovered"] += 1
            
            if not j.get("rejection_record"):
                providers[p]["selected_jobs"] += 1
                
        results = []
        for p in providers.values():
            p["yield_pct"] = round(p["selected_jobs"] / p["jobs_discovered"] * 100, 1) if p["jobs_discovered"] > 0 else 0
            results.append(p)
            
        results.sort(key=lambda x: x["yield_pct"], reverse=True)
        return results
