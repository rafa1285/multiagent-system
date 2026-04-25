"""Factory for resolving active observability provider."""

from __future__ import annotations

from functools import lru_cache

from core import config
from core.observability.base import ObservabilityProvider
from core.observability.exceptions import ObservabilityConfigError
from core.observability.supabase_provider import SupabaseObservabilityProvider


@lru_cache(maxsize=1)
def get_observability_provider() -> ObservabilityProvider:
    provider_name = config.OBSERVABILITY_PROVIDER
    if provider_name == "supabase":
        return SupabaseObservabilityProvider()

    raise ObservabilityConfigError(
        f"Unsupported OBSERVABILITY_PROVIDER: {provider_name}. Supported: supabase"
    )
