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

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from agents.planner.router import router as planner_router
from agents.developer.router import router as developer_router
from agents.reviewer.router import router as reviewer_router
from agents.deployer.router import router as deployer_router
from core.auth import require_api_key
from core.run_state import ensure_run, get_run, list_runs

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


class RunCreateResponse(BaseModel):
    run_id: str
    status: str


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


@app.get("/runs", tags=["Runs"])
def list_run_status(limit: int = Query(default=20, ge=1, le=200), _: None = Depends(require_api_key)) -> dict:
    """List recent runs."""
    return {"items": list_runs(limit=limit)}
