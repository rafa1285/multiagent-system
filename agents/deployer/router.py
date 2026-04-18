"""
HTTP router for the Deployer Agent.

Endpoint:  POST /agents/deployer
Called by: n8n orchestrator (receives output from Reviewer Agent)
"""

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from agents.deployer.agent import DeployerAgent
from core.run_state import ensure_run, update_stage
from providers.open_source import OpenSourceLLMProvider

router = APIRouter(prefix="/agents/deployer", tags=["Deployer"])


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
    run_id = ensure_run(request.run_id)
    update_stage(run_id, "deployer", "running", input_payload={"review": request.review})

    # TODO: inject the provider via dependency injection.
    llm = OpenSourceLLMProvider()
    agent = DeployerAgent(llm=llm)
    try:
        result = agent.run(review=request.review)
    except Exception as exc:
        update_stage(run_id, "deployer", "error", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail={"run_id": run_id, "stage": "deployer", "error": str(exc)},
        ) from exc

    result["run_id"] = run_id
    update_stage(
        run_id,
        "deployer",
        "success",
        output_payload={"agent": result.get("agent"), "status": result.get("status")},
    )
    return DeployerResponse(**result)
