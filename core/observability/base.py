"""Base protocol for observability providers."""

from __future__ import annotations

from typing import Any, Dict, Protocol


class ObservabilityProvider(Protocol):
    def insert_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Insert one observability event and return provider response metadata."""
