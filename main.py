"""
Multi-Agent System – FastAPI application entry point.

Architecture overview
---------------------
This service exposes one HTTP endpoint per agent.  An external orchestrator
(n8n) chains the agents together by calling each endpoint in sequence and
forwarding the response to the next endpoint.

Pipeline:
  n8n  →  POST /agents/planner
       →  POST /agents/developer
       →  POST /agents/reviewer
       →  POST /agents/deployer

Running locally
---------------
    uvicorn main:app --reload

Interactive API docs are available at http://localhost:8000/docs once the
server is running.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from agents.planner.router import router as planner_router
from agents.developer.router import router as developer_router
from agents.reviewer.router import router as reviewer_router
from agents.deployer.router import router as deployer_router
from core import config
from core.auth import require_api_key
from core.observability import ObservabilityConfigError, ObservabilityRequestError, insert_log_event
from core.run_state import ensure_run, get_run, get_run_trace, list_runs

app = FastAPI(
    title="Multi-Agent System",
    description=(
        "HTTP endpoints for the Planner, Developer, Reviewer, and Deployer "
        "agents.  Orchestrated externally by n8n."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Register agent routers
# ---------------------------------------------------------------------------
app.include_router(planner_router)
app.include_router(developer_router)
app.include_router(reviewer_router)
app.include_router(deployer_router)


@app.get("/", tags=["Health"])
def health_check() -> dict:
    """Simple health-check endpoint."""
    return {"status": "ok", "service": "multiagent-system"}


@app.get("/generated-apps/{run_id}", tags=["Generated Apps"], response_class=HTMLResponse)
def get_generated_app(run_id: str) -> HTMLResponse:
    """Serve a generated login+CRUD app materialized by the Deployer stage."""
    app_file = Path(__file__).resolve().parent / "generated_apps" / f"{run_id}.html"
    if not app_file.exists():
        raise HTTPException(status_code=404, detail=f"generated app not found for run_id: {run_id}")
    return HTMLResponse(content=app_file.read_text(encoding="utf-8"))


class RunCreateResponse(BaseModel):
    run_id: str
    status: str


class ObservabilityProbeRequest(BaseModel):
    run_id: Optional[str] = None
    step_name: str = "observability.probe.requested"
    status: str = "started"
    source_system: str = "multiagent-api"

    # Backward-compatible optional fields
    stage: str = "probe"
    level: str = "info"
    message: str = "observability connectivity probe"
    source: str = "multiagent-system"

    metadata: Dict[str, Any] = Field(default_factory=dict)
    row: Optional[Dict[str, Any]] = None


class ObservabilityProbeResponse(BaseModel):
    ok: bool
    status_code: int
    sink: str
    inserted: int
    run_id: Optional[str] = None


@app.post("/runs", tags=["Runs"], response_model=RunCreateResponse)
def create_run(_: None = Depends(require_api_key)) -> RunCreateResponse:
    """Create a new run id for an execution pipeline."""
    run_id = ensure_run()
    return RunCreateResponse(run_id=run_id, status="created")


@app.get("/runs/{run_id}", tags=["Runs"])
def get_run_status(run_id: str, _: None = Depends(require_api_key)) -> dict:
    """Get run state and per-stage details."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"run_id not found: {run_id}")
    return run


@app.get("/runs/{run_id}/trace", tags=["Runs"])
def get_run_trace_endpoint(run_id: str, _: None = Depends(require_api_key)) -> dict:
    """
    Return the full traceability document for a run.

    Includes all external IDs (Jira issue, GitHub commit, deployment URL),
    complete pipeline event timeline, and audit log.
    """
    trace = get_run_trace(run_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"run_id not found: {run_id}")
    return trace


@app.get("/runs", tags=["Runs"])
def list_run_status(limit: int = Query(default=20, ge=1, le=200), _: None = Depends(require_api_key)) -> dict:
    """List recent runs."""
    return {"items": list_runs(limit=limit)}


@app.post("/observability/probe", tags=["Observability"], response_model=ObservabilityProbeResponse)
@app.post("/observability/supabase/probe", tags=["Observability"], response_model=ObservabilityProbeResponse)
def observability_probe(payload: ObservabilityProbeRequest, _: None = Depends(require_api_key)) -> ObservabilityProbeResponse:
    """Insert one probe row using the active observability provider."""
    if not config.SUPABASE_ENABLE_LOG_WRITE:
        raise HTTPException(
            status_code=403,
            detail="Observability write is disabled. Set SUPABASE_ENABLE_LOG_WRITE=true",
        )

    effective_run_id = payload.run_id or str(uuid4())
    event = payload.row or {
        "run_id": effective_run_id,
        "step_name": payload.step_name,
        "status": payload.status,
        "source_system": payload.source_system,
        "metadata": {
            "stage": payload.stage,
            "level": payload.level,
            "message": payload.message,
            "source": payload.source,
            **payload.metadata,
        },
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        result = insert_log_event(event)
    except ObservabilityConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ObservabilityRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    inserted_payload = result.get("data")
    inserted_count = len(inserted_payload) if isinstance(inserted_payload, list) else int(bool(inserted_payload))
    return ObservabilityProbeResponse(
        ok=True,
        status_code=result["status_code"],
        sink=(
            f"{config.OBSERVABILITY_PROVIDER}:"
            f"{(config.SUPABASE_SCHEMA + '.') if config.SUPABASE_SCHEMA else ''}{config.SUPABASE_LOGS_TABLE}"
        ),
        inserted=inserted_count,
        run_id=event.get("run_id"),
    )
