import pytest
from src.search.planner import SearchPlanner

def test_planner_target_providers(monkeypatch):
    planner = SearchPlanner(config_dir="config")
    
    # Mock registry so it returns a mix of providers
    class MockRegistry:
        def provider_info(self):
            return [
                {"name": "naukri", "enabled": True, "lifecycle_state": "production"},
                {"name": "company_careers", "enabled": True, "lifecycle_state": "beta"},
                {"name": "google_jobs", "enabled": True, "lifecycle_state": "experimental"},
                {"name": "wellfound", "enabled": True, "lifecycle_state": "experimental"},
            ]
    
    import src.acquisition.registry
    monkeypatch.setattr(src.acquisition.registry, "ProviderRegistry", MockRegistry)
    
    # 1. include_experimental = False
    planner.user_profile["include_experimental"] = False
    plans = planner.generate_plans()
    
    if plans:
        allowed = plans[0].target_providers
        assert "naukri" in allowed
        assert "company_careers" in allowed
        assert "google_jobs" not in allowed
        assert "wellfound" not in allowed

    # 2. include_experimental = True
    planner.user_profile["include_experimental"] = True
    plans = planner.generate_plans()
    
    if plans:
        allowed = plans[0].target_providers
        assert "naukri" in allowed
        assert "company_careers" in allowed
        assert "google_jobs" in allowed
        assert "wellfound" in allowed
