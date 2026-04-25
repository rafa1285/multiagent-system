"""Supabase observability provider implementation using supabase-py."""

from __future__ import annotations

from typing import Any, Dict

from supabase import Client, create_client

from core import config
from core.observability.exceptions import ObservabilityConfigError, ObservabilityRequestError


class SupabaseObservabilityProvider:
    def __init__(self) -> None:
        self._validate_config()
        self._client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)

    @staticmethod
    def _validate_config() -> None:
        if not config.SUPABASE_URL:
            raise ObservabilityConfigError("SUPABASE_URL is required")
        if not config.SUPABASE_SERVICE_ROLE_KEY:
            raise ObservabilityConfigError("SUPABASE_SERVICE_ROLE_KEY is required")
        if not config.SUPABASE_LOGS_TABLE:
            raise ObservabilityConfigError("SUPABASE_LOGS_TABLE is required")

    @staticmethod
    def _resolve_target() -> tuple[str | None, str]:
        table = config.SUPABASE_LOGS_TABLE.strip()
        schema = config.SUPABASE_SCHEMA.strip() or None

        # Support schema-qualified table names in SUPABASE_LOGS_TABLE for backward compatibility.
        if "." in table and not schema:
            maybe_schema, maybe_table = table.split(".", 1)
            if maybe_schema and maybe_table:
                return maybe_schema, maybe_table

        return schema, table

    def insert_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        schema, table = self._resolve_target()
        try:
            if schema:
                response = self._client.schema(schema).table(table).insert(event).execute()
            else:
                response = self._client.table(table).insert(event).execute()
        except Exception as exc:
            raise ObservabilityRequestError(
                f"Supabase insert failed: {type(exc).__name__}: {exc}"
            ) from exc

        data = getattr(response, "data", None)
        status_code = getattr(response, "status_code", 200)
        return {
            "status_code": int(status_code),
            "data": data,
        }
