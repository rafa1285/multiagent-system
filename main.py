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

from fastapi import FastAPI

from agents.planner.router import router as planner_router
from agents.developer.router import router as developer_router
from agents.reviewer.router import router as reviewer_router
from agents.deployer.router import router as deployer_router

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
