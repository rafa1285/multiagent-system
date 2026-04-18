"""
HTTP router for the Planner Agent.

Endpoint:  POST /agents/planner
Called by: n8n orchestrator
"""

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.planner.agent import PlannerAgent
from core.run_state import ensure_run, update_stage
from providers.open_source import OpenSourceLLMProvider

router = APIRouter(prefix="/agents/planner", tags=["Planner"])


class PlannerRequest(BaseModel):
    """Request body for the Planner endpoint."""

    task: str  # High-level description of what needs to be built.
    run_id: Optional[str] = None


class PlannerResponse(BaseModel):
    """Response body returned by the Planner endpoint."""

    agent: str
    task: str
    plan: str  # TODO: replace with a structured type once the agent is implemented.
    run_id: str


@router.post("", response_model=PlannerResponse, summary="Run the Planner Agent")
def run_planner(request: PlannerRequest) -> PlannerResponse:
    """
    Accepts a high-level task description and returns a structured development
    plan produced by the Planner Agent.

    This stub always uses the open-source LLM provider.  Swap the provider
    instance here (or inject it) when adding Claude support.
    """
    run_id = ensure_run(request.run_id)
    update_stage(
        run_id,
        "planner",
        "running",
        input_payload={"task": request.task},
    )

    # TODO: inject the provider via dependency injection.
    llm = OpenSourceLLMProvider()
    agent = PlannerAgent(llm=llm)
    try:
        result = agent.run(task=request.task)
    except Exception as exc:
        update_stage(run_id, "planner", "error", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail={"run_id": run_id, "stage": "planner", "error": str(exc)},
        ) from exc

    result["run_id"] = run_id
    update_stage(
        run_id,
        "planner",
        "success",
        output_payload={"agent": result.get("agent")},
    )
    return PlannerResponse(**result)
