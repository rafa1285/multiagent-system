"""
HTTP router for the Developer Agent.

Endpoint:  POST /agents/developer
Called by: n8n orchestrator (receives output from Planner Agent)
"""

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from agents.developer.agent import DeveloperAgent
from core.run_state import ensure_run, update_stage
from providers.open_source import OpenSourceLLMProvider

router = APIRouter(prefix="/agents/developer", tags=["Developer"])


class DeveloperRequest(BaseModel):
    """Request body for the Developer endpoint."""

    plan: Any  # Structured plan produced by the PlannerAgent.
    run_id: Optional[str] = None


class DeveloperResponse(BaseModel):
    """Response body returned by the Developer endpoint."""

    agent: str
    plan: Any
    code: str  # TODO: replace with a structured type once the agent is implemented.
    run_id: str


@router.post("", response_model=DeveloperResponse, summary="Run the Developer Agent")
def run_developer(request: DeveloperRequest) -> DeveloperResponse:
    """
    Accepts a development plan and returns generated code artefacts produced
    by the Developer Agent.

    This stub always uses the open-source LLM provider.  Swap the provider
    instance here (or inject it) when adding Claude support.
    """
    run_id = ensure_run(request.run_id)
    update_stage(run_id, "developer", "running", input_payload={"plan": request.plan})

    # TODO: inject the provider via dependency injection.
    llm = OpenSourceLLMProvider()
    agent = DeveloperAgent(llm=llm)
    try:
        result = agent.run(plan=request.plan)
    except Exception as exc:
        update_stage(run_id, "developer", "error", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail={"run_id": run_id, "stage": "developer", "error": str(exc)},
        ) from exc

    result["run_id"] = run_id
    update_stage(
        run_id,
        "developer",
        "success",
        output_payload={"agent": result.get("agent")},
    )
    return DeveloperResponse(**result)
