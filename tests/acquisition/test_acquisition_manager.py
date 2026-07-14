import pytest
from src.acquisition.models import NormalizedJob, SearchPlan, JobProvenance, ProviderCapabilities
from src.acquisition.manager import AcquisitionManager
from src.acquisition.registry import ProviderRegistry
from src.acquisition.provider import JobProvider

class MockCompanyCareers(JobProvider):
    PROVIDER_NAME = "company_careers"
    def initialize(self, config):
        pass
    def capabilities(self):
        return ProviderCapabilities()
    def health(self):
        pass
    def search(self, plan):
        return [NormalizedJob(
            provider="company_careers",
            provider_job_id="1",
            provider_name="Company Careers",
            provider_url="https://company.com/job/1",
            application_url="https://company.com/apply/1",
            job_board="company_careers",
            company="Acme Corp",
            title="Software Engineer",
            description="Build scalable backends.",
            skills=["Python", "FastAPI"],
            provenance=JobProvenance(
                provider="company_careers",
                generated_query="Software Engineer",
                search_profile="backend"
            ),
            provider_metadata={"internal_id": "999"}
        )]
    def normalize(self, raw):
        pass
    def shutdown(self):
        pass

class MockNaukri(JobProvider):
    PROVIDER_NAME = "naukri"
    def initialize(self, config):
        pass
    def capabilities(self):
        return ProviderCapabilities()
    def health(self):
        pass
    def search(self, plan):
        return [NormalizedJob(
            provider="naukri",
            provider_job_id="n1",
            provider_name="Naukri",
            provider_url="https://naukri.com/job/n1",
            application_url="https://company.com/apply/1", # Exact match application_url
            job_board="naukri",
            company="Acme Corp",
            title="Software Engineer",
            description="Build scalable backends. Needs 5 years experience.", # Longest description
            skills=["Java", "Spring"],
            provenance=JobProvenance(
                provider="naukri",
                generated_query="Software Engineer",
                search_profile="backend"
            ),
            provider_metadata={"naukri_score": 9.5}
        )]
    def normalize(self, raw):
        pass
    def shutdown(self):
        pass

class MockRemoteOK(JobProvider):
    PROVIDER_NAME = "remoteok"
    def initialize(self, config):
        pass
    def capabilities(self):
        return ProviderCapabilities()
    def health(self):
        pass
    def search(self, plan):
        return [NormalizedJob(
            provider="remoteok",
            provider_job_id="r1",
            provider_name="RemoteOK",
            provider_url="https://remoteok.com/job/r1",
            application_url="https://company.com/apply/1", # Exact match application_url
            job_board="remoteok",
            company="Acme Corp",
            title="Software Engineer",
            description="Build scalable backends.",
            skills=["Docker", "AWS"],
            provenance=JobProvenance(
                provider="remoteok",
                generated_query="Software Engineer",
                search_profile="backend"
            )
        )]
    def normalize(self, raw):
        pass
    def shutdown(self):
        pass


class MockRegistry(ProviderRegistry):
    def __init__(self):
        self._loaded_providers = [
            MockCompanyCareers(),
            MockNaukri(),
            MockRemoteOK()
        ]
        # Simulate priority sorting
        # company_careers: 100, naukri: 80, remoteok: 50
        self._loaded_providers[0]._config = {"priority": 100}
        self._loaded_providers[1]._config = {"priority": 80}
        self._loaded_providers[2]._config = {"priority": 50}
        self._capabilities_map = {
            "company_careers": ProviderCapabilities(supports_auto_apply=False),
            "naukri": ProviderCapabilities(supports_auto_apply=True),
            "remoteok": ProviderCapabilities(supports_auto_apply=False)
        }
    def enabled_providers(self):
        return self._loaded_providers

def test_cross_provider_canonicalization():
    registry = MockRegistry()
    manager = AcquisitionManager(registry)
    
    plan = SearchPlan(
        profile="backend",
        generated_query="Software Engineer",
        location="Remote"
    )
    
    jobs, summary = manager.acquire([plan])
    
    assert len(jobs) == 1
    assert summary.total_unique_jobs == 1
    assert summary.cross_provider_duplicates == 2
    
    job = jobs[0]
    
    # 1. Verify canonical provider
    assert job.provider == "company_careers"
    
    # 2. Verify also_seen_on merges all sources
    assert hasattr(job, "also_seen_on")
    assert "naukri" in job.also_seen_on
    assert "remoteok" in job.also_seen_on
    
    # 3. Verify metadata merges
    assert hasattr(job, "provider_metadata")
    assert job.provider_metadata["internal_id"] == "999"
    assert job.provider_metadata["naukri_score"] == 9.5
    
    # 4. Verify tags (skills) merge
    assert set(["Python", "FastAPI", "Java", "Spring", "Docker", "AWS"]).issubset(set(job.tags))
    
    # 5. Verify description takes the longest
    assert "Needs 5 years experience." in job.description
    
    # 6. Verify application URLs are preserved
    assert job.apply_link == "https://company.com/apply/1"
