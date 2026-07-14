import yaml
from pathlib import Path

configs = {
    "remotive.yaml": {"enabled": True, "priority": 70},
    "arbeitnow.yaml": {"enabled": True, "priority": 70},
    "hackernews.yaml": {"enabled": True, "priority": 60},
    "company_careers.yaml": {"enabled": True, "priority": 100},
}

for name, data in configs.items():
    with open(f"config/providers/{name}", "w") as f:
        yaml.dump(data, f)

with open("config/company_targets.yaml", "w") as f:
    yaml.dump({
        "companies": [
            "Microsoft", "Google", "Amazon", "Databricks", 
            "Snowflake", "Rubrik", "Anthropic", "OpenAI"
        ]
    }, f)

with open("config/provider_groups.yaml", "w") as f:
    yaml.dump({
        "groups": {
            "India": ["naukri", "foundit", "instahyre"],
            "Global": ["remoteok", "weworkremotely", "remotive", "arbeitnow"],
            "Company": ["company_careers"],
            "Experimental": ["google_jobs", "wellfound"]
        }
    }, f)
