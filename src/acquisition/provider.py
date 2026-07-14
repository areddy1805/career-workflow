"""
src/acquisition/provider.py — Abstract JobProvider interface with self-registration.

Adding a new provider:
  1. Subclass JobProvider, set PROVIDER_NAME = "my_board"
  2. Add config/providers/my_board.yaml
  3. Import the module anywhere (providers/__init__.py is the right place)

No PROVIDER_CLASS_MAP. No pipeline changes. Ever.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from src.acquisition.models import (
    NormalizedJob,
    ProviderCapabilities,
    ProviderHealth,
    ProviderHealthStatus,
    ProviderType,
    SearchPlan,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal self-registration registry
# ---------------------------------------------------------------------------


class _ProviderRegistry:
    """
    Class-level registry of all JobProvider subclasses.

    Populated automatically by JobProvider.__init_subclass__ as modules are
    imported. External code should never write to this directly.
    """
    _registry: dict[str, type[JobProvider]] = {}

    @classmethod
    def register(cls, provider_cls: type) -> None:
        name = getattr(provider_cls, "PROVIDER_NAME", "")
        if name:
            if name in cls._registry:
                logger.warning(
                    "Provider '%s' already registered (overwriting with %s)",
                    name,
                    provider_cls.__name__,
                )
            cls._registry[name] = provider_cls
            logger.debug("Registered provider: %s -> %s", name, provider_cls.__name__)

    @classmethod
    def get(cls, name: str) -> type[JobProvider] | None:
        return cls._registry.get(name)

    @classmethod
    def all_names(cls) -> list[str]:
        return list(cls._registry.keys())

    @classmethod
    def all_classes(cls) -> dict[str, type[JobProvider]]:
        return dict(cls._registry)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class JobProvider(ABC):
    """
    Abstract base class for all job acquisition providers.

    Every concrete subclass MUST set:
        PROVIDER_NAME: str  — must match config/providers/{name}.yaml filename stem
        PROVIDER_TYPE: ProviderType

    Self-registration is automatic via __init_subclass__. The registry is
    populated when the provider module is imported — providers/__init__.py
    handles all imports.
    """

    PROVIDER_NAME: str = ""
    PROVIDER_TYPE: ProviderType = ProviderType.JOB_BOARD

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Only register concrete classes that declare a name
        if cls.PROVIDER_NAME:
            _ProviderRegistry.register(cls)

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._initialized: bool = False

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """
        One-time setup using the provider's YAML config dict.
        Called by ProviderRegistry before any search().
        Must be idempotent (registry may call it again on reconnect).
        """

    @abstractmethod
    def search(self, plan: SearchPlan) -> list[NormalizedJob]:
        """
        Execute one search plan and return normalized jobs.

        Must handle its own errors gracefully. Returning [] on failure is
        preferable to raising, so other providers can still contribute.
        Failures should be logged and reflected in health().
        """

    @abstractmethod
    def normalize(self, raw: Any) -> NormalizedJob:
        """
        Map provider-raw data to NormalizedJob.
        Called internally by search(); exposed separately for unit testing.
        """

    @abstractmethod
    def health(self) -> ProviderHealth:
        """
        Return current health status. Should be non-blocking (no heavy I/O).
        The registry calls this before including a provider in a run.
        """

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """
        Return static capabilities. Called once at registry load time.
        Used by AcquisitionManager to route jobs to correct queues.
        """

    @abstractmethod
    def shutdown(self) -> None:
        """
        Teardown resources (close sessions, browsers, DB connections).
        Called by AcquisitionManager at the end of each acquisition run.
        """

    # ------------------------------------------------------------------
    # Helpers available to all subclasses
    # ------------------------------------------------------------------

    def _cfg(self, key: str, default: Any = None) -> Any:
        """Convenience accessor for config values."""
        return self._config.get(key, default)

    def _max_pages(self) -> int:
        return int(self._cfg("max_pages", 3))

    def _search_delay(self) -> float:
        return float(self._cfg("search_delay", 1.2))

    def _max_results(self) -> int:
        return int(self._cfg("max_results", 100))

    def _user_agent(self) -> str:
        return self._cfg(
            "user_agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36",
        )

    def _connect_timeout(self) -> int:
        t = self._cfg("timeouts", {})
        return t.get("connect", 10) if isinstance(t, dict) else 10

    def _read_timeout(self) -> int:
        t = self._cfg("timeouts", {})
        return t.get("read", 30) if isinstance(t, dict) else 30

    def _make_unavailable_health(self, error: str = "") -> ProviderHealth:
        return ProviderHealth(
            provider=self.PROVIDER_NAME,
            status=ProviderHealthStatus.UNAVAILABLE,
            error=error,
        )

    def _make_healthy(self, latency_ms: float = 0.0) -> ProviderHealth:
        return ProviderHealth(
            provider=self.PROVIDER_NAME,
            status=ProviderHealthStatus.HEALTHY,
            latency_ms=latency_ms,
        )
