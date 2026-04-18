"""In-memory run state tracking for multi-agent executions.

This module provides a minimal state machine per run_id so external
orchestrators can correlate and inspect pipeline progress.
"""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4


_RUNS: Dict[str, Dict[str, Any]] = {}
_LOCK = Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_run(run_id: Optional[str] = None) -> str:
    """Create the run if needed and return its id."""
    rid = (run_id or "").strip() or str(uuid4())
    now = _now_iso()

    with _LOCK:
        if rid not in _RUNS:
            _RUNS[rid] = {
                "run_id": rid,
                "status": "created",
                "created_at": now,
                "updated_at": now,
                "current_stage": None,
                "stages": {},
                "events": [],
            }

    return rid


def update_stage(
    run_id: str,
    stage: str,
    stage_status: str,
    *,
    input_payload: Optional[Dict[str, Any]] = None,
    output_payload: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Update one stage and append an event to the run history."""
    rid = ensure_run(run_id)
    now = _now_iso()

    with _LOCK:
        run = _RUNS[rid]
        run["updated_at"] = now
        run["current_stage"] = stage

        stage_state: Dict[str, Any] = {
            "status": stage_status,
            "updated_at": now,
        }
        if input_payload is not None:
            stage_state["input"] = input_payload
        if output_payload is not None:
            stage_state["output"] = output_payload
        if error:
            stage_state["error"] = error

        run["stages"][stage] = stage_state
        run["events"].append(
            {
                "at": now,
                "stage": stage,
                "status": stage_status,
                "error": error,
            }
        )

        if stage_status == "error":
            run["status"] = "error"
        elif stage == "deployer" and stage_status == "success":
            run["status"] = "completed"
        else:
            run["status"] = "running"

        return run.copy()


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    """Return one run snapshot."""
    with _LOCK:
        run = _RUNS.get(run_id)
        return run.copy() if run else None


def list_runs(limit: int = 20) -> List[Dict[str, Any]]:
    """Return latest runs sorted by update timestamp desc."""
    safe_limit = max(1, min(limit, 200))
    with _LOCK:
        items = list(_RUNS.values())

    items.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
    return [item.copy() for item in items[:safe_limit]]
