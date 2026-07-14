"""Tests that all provider YAML configs load without error and have required keys."""
from __future__ import annotations

import pytest
import yaml
from pathlib import Path

PROVIDERS_DIR = Path("config/providers")
REQUIRED_KEYS = {"enabled", "priority"}


def _all_provider_yamls():
    if not PROVIDERS_DIR.exists():
        return []
    return list(PROVIDERS_DIR.glob("*.yaml"))


@pytest.mark.parametrize("yaml_path", _all_provider_yamls(), ids=lambda p: p.stem)
def test_provider_yaml_loads(yaml_path: Path):
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data is not None, f"{yaml_path.name} is empty"
    assert isinstance(data, dict), f"{yaml_path.name} must be a dict"


@pytest.mark.parametrize("yaml_path", _all_provider_yamls(), ids=lambda p: p.stem)
def test_provider_yaml_required_keys(yaml_path: Path):
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    for key in REQUIRED_KEYS:
        assert key in data, f"{yaml_path.name} missing required key: {key!r}"


@pytest.mark.parametrize("yaml_path", _all_provider_yamls(), ids=lambda p: p.stem)
def test_provider_priority_valid(yaml_path: Path):
    from src.acquisition.models import ProviderPriority
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    priority = data.get("priority", "normal")
    valid = {e.value for e in ProviderPriority}
    assert priority in valid, f"{yaml_path.name}: priority={priority!r} not in {valid}"


def test_provider_groups_yaml_loads():
    groups_path = Path("config/provider_groups.yaml")
    if not groups_path.exists():
        pytest.skip("provider_groups.yaml not found")
    with open(groups_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    assert "groups" in data
    for group_name, members in data["groups"].items():
        assert isinstance(members, list), f"Group {group_name!r} must be a list"
