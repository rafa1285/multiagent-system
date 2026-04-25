"""Observability service facade used by HTTP endpoints and business logic."""

from __future__ import annotations

from typing import Any, Dict

from core.observability.factory import get_observability_provider


def insert_log_event(event: Dict[str, Any]) -> Dict[str, Any]:
    provider = get_observability_provider()
    return provider.insert_event(event)
