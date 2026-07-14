"""
src/acquisition/registry.py — Provider discovery, loading, and lifecycle management.

The registry is the single source of truth for which providers are active.
It reads config/providers/*.yaml and config/provider_groups.yaml,
auto-discovers registered subclasses (via self-registration), and validates
configuration before handing providers to AcquisitionManager.
"""
from __future__ import annotations

import importlib
import logging
import time
from pathlib import Path
from typing import Any

import yaml

from src.acquisition.models import (
    ProviderCapabilities,
    ProviderHealth,
    ProviderHealthStatus,
    ProviderPriority,
)
from src.acquisition.provider import JobProvider, _ProviderRegistry

logger = logging.getLogger(__name__)

_PROVIDERS_CONFIG_DIR = Path("config/providers")
_GROUPS_CONFIG_PATH = Path("config/provider_groups.yaml")
_USER_PROFILE_PATH = Path("config/user_profile.yaml")

# All provider modules — importing them triggers self-registration
_PROVIDER_MODULES = [
    "src.acquisition.providers.naukri",
    "src.acquisition.providers.remoteok",
    "src.acquisition.providers.weworkremotely",
    "src.acquisition.providers.google_jobs",
    "src.acquisition.providers.wellfound",
    "src.acquisition.providers.instahyre",
    "src.acquisition.providers.foundit",
]


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:
        logger.warning("Failed to load YAML %s: %s", path, exc)
        return {}


def _import_all_providers() -> None:
    """Import all provider modules to trigger self-registration."""
    for module_path in _PROVIDER_MODULES:
        try:
            importlib.import_module(module_path)
        except ImportError as exc:
            logger.debug("Provider module not available: %s — %s", module_path, exc)
        except Exception as exc:
            logger.warning("Error importing provider module %s: %s", module_path, exc)


class ProviderRegistry:
    """
    Discovers, loads, and manages all job acquisition providers.

    Usage:
        registry = ProviderRegistry()
        for provider in registry.enabled_providers():
            jobs = provider.search(plan)
    """

    def __init__(
        self,
        config_dir: str | Path = _PROVIDERS_CONFIG_DIR,
        groups_config: str | Path = _GROUPS_CONFIG_PATH,
        user_profile: str | Path = _USER_PROFILE_PATH,
    ) -> None:
        self._config_dir = Path(config_dir)
        self._groups_config = Path(groups_config)
        self._user_profile_path = Path(user_profile)

        self._provider_configs: dict[str, dict] = {}
        self._loaded_providers: list[JobProvider] = []
        self._capabilities_map: dict[str, ProviderCapabilities] = {}
        self._health_cache: dict[str, ProviderHealth] = {}

        _import_all_providers()
        self._load()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self) -> None:
        self._provider_configs = self._discover_configs()
        enabled_names = self._resolve_enabled_providers()

        for name in enabled_names:
            config = self._provider_configs.get(name, {})
            if not config.get("enabled", False):
                logger.debug("Provider '%s' disabled in config", name)
                continue

            provider_cls = _ProviderRegistry.get(name)
            if provider_cls is None:
                logger.warning(
                    "Provider '%s' has YAML config but no registered class. "
                    "Make sure its module is importable.",
                    name,
                )
                continue

            try:
                provider = provider_cls()
                provider.initialize(config)
                provider._config = config
                provider._initialized = True
                self._loaded_providers.append(provider)
                self._capabilities_map[name] = provider.capabilities()
                logger.info("Loaded provider: %s", name)
            except Exception as exc:
                logger.error("Failed to initialize provider '%s': %s", name, exc)

        # Sort by priority
        self._loaded_providers.sort(
            key=lambda p: ProviderPriority(
                p._cfg("priority", "normal")
            ).to_int()
        )

        logger.info(
            "ProviderRegistry loaded %d provider(s): %s",
            len(self._loaded_providers),
            [p.PROVIDER_NAME for p in self._loaded_providers],
        )

    def _discover_configs(self) -> dict[str, dict]:
        """Load all *.yaml files from config/providers/."""
        configs: dict[str, dict] = {}
        if not self._config_dir.exists():
            return configs
        for path in self._config_dir.glob("*.yaml"):
            name = path.stem
            configs[name] = _load_yaml(path)
            logger.debug("Found provider config: %s", name)
        return configs

    def _resolve_enabled_providers(self) -> list[str]:
        """
        Resolve which providers should be enabled.

        Priority:
          1. Explicit 'enabled: true' in individual YAML → always included
          2. user_profile.yaml 'enabled_provider_groups' → resolve via provider_groups.yaml
          3. If no groups configured → fall through to individual YAML enabled flags
        """
        user_profile = _load_yaml(self._user_profile_path)
        groups_config = _load_yaml(self._groups_config)

        enabled_groups = user_profile.get("enabled_provider_groups", [])
        group_definitions = groups_config.get("groups", {})

        if enabled_groups and group_definitions:
            # Resolve groups → provider names
            resolved: list[str] = []
            for group_name in enabled_groups:
                members = group_definitions.get(group_name, [])
                for member in members:
                    if member not in resolved:
                        resolved.append(member)
            # Also include any providers individually marked enabled
            for name, cfg in self._provider_configs.items():
                if cfg.get("enabled", False) and name not in resolved:
                    resolved.append(name)
            return resolved

        # No groups — use individual YAML enabled flags
        return [
            name for name, cfg in self._provider_configs.items()
            if cfg.get("enabled", False)
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enabled_providers(self) -> list[JobProvider]:
        """Return all loaded, enabled providers sorted by priority."""
        return list(self._loaded_providers)

    def get_provider(self, name: str) -> JobProvider | None:
        for p in self._loaded_providers:
            if p.PROVIDER_NAME == name:
                return p
        return None

    def capabilities_map(self) -> dict[str, ProviderCapabilities]:
        """Map of provider_name → ProviderCapabilities for all loaded providers."""
        return dict(self._capabilities_map)

    def supports_auto_apply_map(self) -> dict[str, bool]:
        """Quick map of {provider_name: supports_auto_apply}."""
        return {
            name: caps.supports_auto_apply
            for name, caps in self._capabilities_map.items()
        }

    def provider_info(self) -> list[dict[str, Any]]:
        """Summary dicts for all known providers (loaded or not) for the API."""
        result = []
        all_registered = _ProviderRegistry.all_names()
        for name in set(list(self._provider_configs.keys()) + all_registered):
            cfg = self._provider_configs.get(name, {})
            loaded = self.get_provider(name)
            caps = self._capabilities_map.get(name)
            health = self._health_cache.get(name)
            result.append({
                "name": name,
                "enabled": cfg.get("enabled", False),
                "priority": cfg.get("priority", "normal"),
                "loaded": loaded is not None,
                "provider_type": getattr(loaded, "PROVIDER_TYPE", {}).value if loaded else "unknown",
                "capabilities": caps.to_dict() if caps else {},
                "health": health.to_dict() if health else None,
                "authentication_required": cfg.get("authentication_required", False),
                "supports_auto_apply": cfg.get("supports_auto_apply", False),
            })
        return sorted(result, key=lambda x: (not x["loaded"], x["name"]))

    def run_health_checks(self) -> dict[str, ProviderHealth]:
        """Run health checks on all loaded providers. Updates internal cache."""
        results: dict[str, ProviderHealth] = {}
        for provider in self._loaded_providers:
            t0 = time.perf_counter()
            try:
                health = provider.health()
                health.latency_ms = (time.perf_counter() - t0) * 1000
            except Exception as exc:
                health = ProviderHealth(
                    provider=provider.PROVIDER_NAME,
                    status=ProviderHealthStatus.UNAVAILABLE,
                    error=str(exc),
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
            results[provider.PROVIDER_NAME] = health
            self._health_cache[provider.PROVIDER_NAME] = health
            logger.debug(
                "Health check: %s -> %s (%.1fms)",
                provider.PROVIDER_NAME,
                health.status.value,
                health.latency_ms,
            )
        return results

    def shutdown_all(self) -> None:
        """Shutdown all loaded providers gracefully."""
        for provider in self._loaded_providers:
            try:
                provider.shutdown()
                logger.debug("Shut down provider: %s", provider.PROVIDER_NAME)
            except Exception as exc:
                logger.warning("Error shutting down %s: %s", provider.PROVIDER_NAME, exc)
