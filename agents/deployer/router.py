"""
HTTP router for the Deployer Agent.

Endpoint:  POST /agents/deployer
Called by: n8n orchestrator (receives output from Reviewer Agent)
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from agents.deployer.agent import DeployerAgent
from core.auth import require_api_key
from core.run_state import StageRetryLimitExceededError, finish_stage_error, finish_stage_success, start_stage
from providers import get_llm_provider

router = APIRouter(prefix="/agents/deployer", tags=["Deployer"], dependencies=[Depends(require_api_key)])


class DeployerRequest(BaseModel):
    """Request body for the Deployer endpoint."""

    review: Any  # Review output produced by the ReviewerAgent.
    run_id: Optional[str] = None


class DeployerResponse(BaseModel):
    """Response body returned by the Deployer endpoint."""

    agent: str
    review: Any
    deployment: str  # TODO: replace with a structured type once the agent is implemented.
    status: str
    run_id: str


@router.post("", response_model=DeployerResponse, summary="Run the Deployer Agent")
def run_deployer(request: DeployerRequest) -> DeployerResponse:
    """
    Accepts a code review and triggers deployment steps, returning the
    deployment status produced by the Deployer Agent.

    This stub always uses the open-source LLM provider.  Swap the provider
    instance here (or inject it) when adding Claude support.
    """
    try:
        attempt = start_stage(request.run_id, "deployer", {"review": request.review})
    except StageRetryLimitExceededError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if attempt["cached"]:
        cached = attempt["output_payload"]
        return DeployerResponse(**cached)

    run_id = attempt["run_id"]

    llm = get_llm_provider()
    agent = DeployerAgent(llm=llm)
    try:
        result = agent.run(review=request.review)
    except Exception as exc:
        finish_stage_error(run_id, "deployer", attempt["attempt_id"], str(exc))
        raise HTTPException(
            status_code=500,
            detail={"run_id": run_id, "stage": "deployer", "error": str(exc)},
        ) from exc

    result["run_id"] = run_id
    finish_stage_success(run_id, "deployer", attempt["attempt_id"], result)
    return DeployerResponse(**result)
