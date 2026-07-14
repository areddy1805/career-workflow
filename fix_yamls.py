import yaml
from pathlib import Path

providers_dir = Path("config/providers")
priority_map = {
    "critical": 100,
    "high": 80,
    "normal": 50,
    "low": 20
}

for path in providers_dir.glob("*.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    if "priority" in data and isinstance(data["priority"], str):
        str_prio = data["priority"].lower()
        if str_prio in priority_map:
            data["priority"] = priority_map[str_prio]
            
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f)
            print(f"Updated {path.name} priority to {data['priority']}")
