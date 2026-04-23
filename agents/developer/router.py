"""
HTTP router for the Developer Agent.

Endpoint:  POST /agents/developer
Called by: n8n orchestrator (receives output from Planner Agent)
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from agents.developer.agent import DeveloperAgent
from core.auth import require_api_key
from core.run_state import StageRetryLimitExceededError, finish_stage_error, finish_stage_success, start_stage
from providers import get_llm_provider

router = APIRouter(prefix="/agents/developer", tags=["Developer"], dependencies=[Depends(require_api_key)])


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
    try:
        attempt = start_stage(request.run_id, "developer", {"plan": request.plan})
    except StageRetryLimitExceededError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if attempt["cached"]:
        cached = attempt["output_payload"]
        return DeveloperResponse(**cached)

    run_id = attempt["run_id"]

    llm = get_llm_provider()
    agent = DeveloperAgent(llm=llm)
    try:
        result = agent.run(plan=request.plan)
    except Exception as exc:
        finish_stage_error(run_id, "developer", attempt["attempt_id"], str(exc))
        raise HTTPException(
            status_code=500,
            detail={"run_id": run_id, "stage": "developer", "error": str(exc)},
        ) from exc

    result["run_id"] = run_id
    finish_stage_success(run_id, "developer", attempt["attempt_id"], result)
    return DeveloperResponse(**result)
