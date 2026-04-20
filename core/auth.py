"""Authentication helpers for multiagent HTTP endpoints."""

from fastapi import Header, HTTPException

from core import config


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected_key = config.MULTIAGENT_API_KEY
    if not expected_key:
        return
    if x_api_key == expected_key:
        return
    raise HTTPException(status_code=401, detail="Invalid or missing API key")