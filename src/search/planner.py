import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class SearchQuery:
    keyword: str
    location: str
    track: str
    weight: float = 1.0
    search_profile: str = "unknown"
    matched_technology: str = ""

    def to_dict(self):
        return {
            "keyword": self.keyword,
            "location": self.location,
            "track": self.track,
            "search_profile": self.search_profile,
            "matched_technology": self.matched_technology
        }

class SearchPlanner:
    """
    SearchPlanner is responsible for generating acquisition queries based on user configuration.
    It reads YAML files from the config directory and generates a deduplicated list of search queries.
    """
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.user_profile = self._load_yaml(self.config_dir / "user_profile.yaml")
        self.planner_config = self._load_yaml(self.config_dir / "search" / "planner.yaml")
        
        self.search_profiles = {}
        self.technology_profiles = {}
        self.company_profiles = {}
        self.negative_profiles = {}
        
        self._load_profiles("search_profiles", self.search_profiles)
        self._load_profiles("technology_profiles", self.technology_profiles)
        self._load_profiles("company_profiles", self.company_profiles)
        self._load_profiles("negative_profiles", self.negative_profiles)
        
        self._validate_configs()

    def _validate_configs(self):
        """Validates that all cross-references exist and are not cyclic."""
        active = self.user_profile.get("active_profiles", [])
        for prof in active:
            if prof not in self.search_profiles:
                raise ValueError(f"Active profile '{prof}' referenced in user_profile.yaml but not found in search_profiles/")
        
        for name, profile in self.search_profiles.items():
            for tech in profile.get("preferred_technologies", []):
                if tech not in self.technology_profiles:
                    # Allowing direct keywords as fallback, but log a warning to encourage taxonomy use
                    logger.debug(f"Technology reference '{tech}' in '{name}' not found in technology_profiles. Using as raw keyword.")
            
            for neg in profile.get("negative_groups", []):
                if neg not in self.negative_profiles:
                    raise ValueError(f"Negative group '{neg}' in '{name}' not found in negative_profiles/")

    def _load_yaml(self, path: Path) -> dict:
        if not path.exists():
            logger.warning(f"Configuration file not found: {path}")
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            return {}

    def _load_profiles(self, directory: str, store: dict):
        dir_path = self.config_dir / directory
        if not dir_path.exists():
            return
        
        for file_path in dir_path.glob("*.yaml"):
            store[file_path.stem] = self._load_yaml(file_path)

    def generate_queries(self) -> list[dict]:
        """
        Generates and deduplicates search queries.
        Returns a list of dictionaries compatible with the legacy SEARCH_TRACKS interface.
        """
        active_profiles = self.user_profile.get("active_profiles", [])
        locations = self.user_profile.get("preferred_locations", ["Pune"])
        
        max_queries = self.planner_config.get("max_queries_per_profile", 15)
        
        generated_queries = set()
        
        for profile_name in active_profiles:
            profile = self.search_profiles.get(profile_name)
            if not profile:
                continue
                
            titles = profile.get("titles", [])
            weight = profile.get("weight", 1.0)
            
            # Legacy track mapping based on weight
            track = "TIER_C"
            if weight >= 1.2:
                track = "TIER_S"
            elif weight >= 1.1:
                track = "TIER_A"
            elif weight >= 1.0:
                track = "TIER_B"
                
            # Expand technology keywords
            tech_keywords = []
            for tech_ref in profile.get("preferred_technologies", []):
                if tech_ref in self.technology_profiles:
                    tech_keywords.extend(self.technology_profiles[tech_ref].get("keywords", []))
                else:
                    tech_keywords.append(tech_ref) # direct keyword fallback
                    
            # Expand negative keywords
            negative_keywords = []
            for neg_ref in profile.get("negative_groups", []):
                if neg_ref in self.negative_profiles:
                    negative_keywords.extend(self.negative_profiles[neg_ref].get("keywords", []))
            
            neg_suffix = " ".join(f"-{neg}" for neg in negative_keywords)
            if neg_suffix:
                neg_suffix = f" {neg_suffix}"
                    
            profile_queries = []
            
            for location in locations:
                for title in titles:
                    # 1. Role-centric query
                    profile_queries.append(SearchQuery(keyword=f"{title}{neg_suffix}", location=location, track=track, weight=weight, search_profile=profile_name, matched_technology="role_only"))
                    
                    # 2. Role + Technology query
                    for tech in tech_keywords[:max_queries]: 
                        query_str = f"{title} {tech}{neg_suffix}"
                        profile_queries.append(SearchQuery(keyword=query_str, location=location, track=track, weight=weight, search_profile=profile_name, matched_technology=tech))
                        
            # Apply limit per profile to prevent explosion
            profile_queries = profile_queries[:max_queries]
            
            for q in profile_queries:
                generated_queries.add((q.keyword, q.location, q.track, q.search_profile, q.matched_technology))

        # Convert back to legacy dict format
        result = [
            {"keyword": kw, "location": loc, "track": trk, "search_profile": prof, "matched_technology": tech}
            for kw, loc, trk, prof, tech in generated_queries
        ]
        
        # Sort for deterministic output
        result.sort(key=lambda x: x["keyword"])
        return result


    def generate_plans(self) -> "list":
        """
        Generate SearchPlan objects for the provider-based acquisition layer.

        Alongside the existing generate_queries() method (which remains unchanged
        for backward compatibility), this method returns richer SearchPlan objects
        understood by AcquisitionManager.

        SearchPlan carries the full context needed by any provider:
        - location, country, experience, work_mode, remote_policy
        - technology_group for provenance tracking
        - target_providers / provider_filters (empty = all enabled)
        - priority, weight for resource allocation
        """
        from src.acquisition.models import SearchPlan
        from src.acquisition.registry import ProviderRegistry

        registry = ProviderRegistry()
        include_exp = self.user_profile.get("include_experimental", False)
        allowed_providers = []
        for p_info in registry.provider_info():
            if p_info["enabled"]:
                state = p_info.get("lifecycle_state", "production")
                if state in ("disabled", "deprecated"):
                    continue
                if state == "experimental" and not include_exp:
                    continue
                allowed_providers.append(p_info["name"])

        active_profiles = self.user_profile.get("active_profiles", [])
        locations = self.user_profile.get("preferred_locations", ["Pune"])
        country = self.user_profile.get("country", "IN")
        default_experience_levels = self.user_profile.get("experience_levels", [2, 4, 6])
        remote_policy = self.user_profile.get("remote_policy", "")

        max_queries = self.planner_config.get("max_queries_per_profile", 10)

        plans: list[SearchPlan] = []
        seen: set[tuple] = set()

        for profile_name in active_profiles:
            profile = self.search_profiles.get(profile_name)
            if not profile:
                continue

            titles = profile.get("titles", [])
            weight = profile.get("weight", 1.0)
            work_mode = profile.get("work_mode", "")

            # Map weight → priority integer
            if weight >= 1.2:
                priority = 100
                track = "TIER_S"
            elif weight >= 1.1:
                priority = 80
                track = "TIER_A"
            elif weight >= 1.0:
                priority = 50
                track = "TIER_B"
            else:
                priority = 20
                track = "TIER_C"

            # Expand technology profiles
            tech_keywords: list[tuple[str, str]] = []  # (keyword, tech_group_name)
            for tech_ref in profile.get("preferred_technologies", []):
                if tech_ref in self.technology_profiles:
                    for kw in self.technology_profiles[tech_ref].get("keywords", []):
                        tech_keywords.append((kw, tech_ref))
                else:
                    tech_keywords.append((tech_ref, tech_ref))

            # Expand negative keywords
            negative_keywords = []
            for neg_ref in profile.get("negative_groups", []):
                if neg_ref in self.negative_profiles:
                    negative_keywords.extend(self.negative_profiles[neg_ref].get("keywords", []))

            neg_suffix = " ".join(f"-{neg}" for neg in negative_keywords)
            if neg_suffix:
                neg_suffix = f" {neg_suffix}"

            profile_plans = []

            for location in locations:
                for title in titles:
                    for exp in default_experience_levels:
                        # Role-only plan
                        query = f"{title}{neg_suffix}"
                        key = (query, location, exp, profile_name, "role_only")
                        if key not in seen:
                            seen.add(key)
                            profile_plans.append(SearchPlan(
                                profile=profile_name,
                                generated_query=query,
                                location=location,
                                country=country,
                                experience=exp,
                                work_mode=work_mode,
                                remote_policy=remote_policy,
                                priority=priority,
                                weight=weight,
                                track=track,
                                matched_technology="role_only",
                                technology_group="",
                                target_providers=list(allowed_providers),
                            ))

                        # Role + technology plans
                        for tech_kw, tech_group in tech_keywords[:max_queries]:
                            query = f"{title} {tech_kw}{neg_suffix}"
                            key = (query, location, exp, profile_name, tech_group)
                            if key not in seen:
                                seen.add(key)
                                profile_plans.append(SearchPlan(
                                    profile=profile_name,
                                    generated_query=query,
                                    location=location,
                                    country=country,
                                    experience=exp,
                                    work_mode=work_mode,
                                    remote_policy=remote_policy,
                                    priority=priority,
                                    weight=weight,
                                    track=track,
                                    matched_technology=tech_kw,
                                    technology_group=tech_group,
                                    target_providers=list(allowed_providers),
                                ))

            plans.extend(profile_plans[:max_queries])

        plans.sort(key=lambda p: (p.priority, p.generated_query), reverse=True)
        return plans
