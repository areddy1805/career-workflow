"""Tests for ProviderRegistry: discovery, loading, priority, group resolution."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile, os, yaml

from src.acquisition.models import ProviderCapabilities, ProviderHealth, ProviderHealthStatus, SearchPlan
from src.acquisition.provider import JobProvider, _ProviderRegistry
from src.acquisition.models import NormalizedJob, JobProvenance, ProviderType


# ---------------------------------------------------------------------------
# Helpers — minimal concrete provider for testing
# ---------------------------------------------------------------------------

class _DummyProvider(JobProvider):
    PROVIDER_NAME = "_test_dummy"
    PROVIDER_TYPE = ProviderType.JOB_BOARD

    def initialize(self, config): self._config = config; self._initialized = True
    def search(self, plan): return []
    def normalize(self, raw): raise NotImplementedError
    def health(self): return ProviderHealth(provider=self.PROVIDER_NAME, status=ProviderHealthStatus.HEALTHY)
    def capabilities(self): return ProviderCapabilities()
    def shutdown(self): pass


# ---------------------------------------------------------------------------
# Self-registration
# ---------------------------------------------------------------------------

def test_self_registration():
    """Provider registers itself automatically when class is defined."""
    registered = _ProviderRegistry.all_names()
    assert "_test_dummy" in registered


def test_get_registered_class():
    cls = _ProviderRegistry.get("_test_dummy")
    assert cls is _DummyProvider


def test_provider_instantiates():
    p = _DummyProvider()
    p.initialize({})
    assert p._initialized is True


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

def _make_temp_config(providers: dict[str, dict], groups: dict | None = None) -> Path:
    """Write provider YAML files to a temp directory. Returns config_dir."""
    tmp = Path(tempfile.mkdtemp())
    providers_dir = tmp / "providers"
    providers_dir.mkdir()
    for name, cfg in providers.items():
        (providers_dir / f"{name}.yaml").write_text(yaml.dump(cfg))
    if groups:
        (tmp / "provider_groups.yaml").write_text(yaml.dump(groups))
    return providers_dir, tmp


def test_registry_loads_enabled_provider():
    """Registry loads providers that have enabled:true and a registered class."""
    providers_dir, tmp = _make_temp_config({
        "_test_dummy": {"enabled": True, "priority": "normal"}
    })

    from src.acquisition.registry import ProviderRegistry
    registry = ProviderRegistry(config_dir=providers_dir, groups_config=tmp / "missing.yaml", user_profile=tmp / "missing.yaml")
    loaded = [p.PROVIDER_NAME for p in registry.enabled_providers()]
    assert "_test_dummy" in loaded


def test_registry_skips_disabled_provider():
    providers_dir, tmp = _make_temp_config({
        "_test_dummy": {"enabled": False, "priority": "normal"}
    })
    from src.acquisition.registry import ProviderRegistry
    registry = ProviderRegistry(config_dir=providers_dir, groups_config=tmp / "missing.yaml", user_profile=tmp / "missing.yaml")
    loaded = [p.PROVIDER_NAME for p in registry.enabled_providers()]
    assert "_test_dummy" not in loaded


def test_registry_priority_sort():
    """Providers are sorted by priority (critical first, low last)."""
    # Register two test providers with different priorities
    class _LowP(JobProvider):
        PROVIDER_NAME = "_test_low"
        PROVIDER_TYPE = ProviderType.JOB_BOARD
        def initialize(self, c): self._config = c; self._initialized = True
        def search(self, p): return []
        def normalize(self, r): raise NotImplementedError
        def health(self): return ProviderHealth(provider=self.PROVIDER_NAME, status=ProviderHealthStatus.HEALTHY)
        def capabilities(self): return ProviderCapabilities()
        def shutdown(self): pass

    class _CritP(JobProvider):
        PROVIDER_NAME = "_test_crit"
        PROVIDER_TYPE = ProviderType.JOB_BOARD
        def initialize(self, c): self._config = c; self._initialized = True
        def search(self, p): return []
        def normalize(self, r): raise NotImplementedError
        def health(self): return ProviderHealth(provider=self.PROVIDER_NAME, status=ProviderHealthStatus.HEALTHY)
        def capabilities(self): return ProviderCapabilities()
        def shutdown(self): pass

    providers_dir, tmp = _make_temp_config({
        "_test_low":  {"enabled": True, "priority": "low"},
        "_test_crit": {"enabled": True, "priority": "critical"},
    })
    from src.acquisition.registry import ProviderRegistry
    registry = ProviderRegistry(config_dir=providers_dir, groups_config=tmp / "missing.yaml", user_profile=tmp / "missing.yaml")
    names = [p.PROVIDER_NAME for p in registry.enabled_providers()]
    assert names.index("_test_crit") < names.index("_test_low")


def test_registry_unknown_provider_warn_only(caplog):
    """A YAML with no matching registered class logs a warning but does not crash."""
    providers_dir, tmp = _make_temp_config({
        "_not_registered": {"enabled": True, "priority": "normal"}
    })
    from src.acquisition.registry import ProviderRegistry
    import logging
    with caplog.at_level(logging.WARNING, logger="src.acquisition.registry"):
        registry = ProviderRegistry(config_dir=providers_dir, groups_config=tmp / "missing.yaml", user_profile=tmp / "missing.yaml")
    loaded = registry.enabled_providers()
    assert all(p.PROVIDER_NAME != "_not_registered" for p in loaded)
