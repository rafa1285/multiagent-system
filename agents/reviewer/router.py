"""
HTTP router for the Reviewer Agent.

Endpoint:  POST /agents/reviewer
Called by: n8n orchestrator (receives output from Developer Agent)
"""

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from agents.reviewer.agent import ReviewerAgent
from core.run_state import ensure_run, update_stage
from providers.open_source import OpenSourceLLMProvider

router = APIRouter(prefix="/agents/reviewer", tags=["Reviewer"])


class ReviewerRequest(BaseModel):
    """Request body for the Reviewer endpoint."""

    code: Any  # Code artefacts produced by the DeveloperAgent.
    run_id: Optional[str] = None


class ReviewerResponse(BaseModel):
    """Response body returned by the Reviewer endpoint."""

    agent: str
    code: Any
    review: str  # TODO: replace with a structured type once the agent is implemented.
    approved: bool
    run_id: str


@router.post("", response_model=ReviewerResponse, summary="Run the Reviewer Agent")
def run_reviewer(request: ReviewerRequest) -> ReviewerResponse:
    """
    Accepts generated code artefacts and returns a code review with a
    pass/fail verdict produced by the Reviewer Agent.

    This stub always uses the open-source LLM provider.  Swap the provider
    instance here (or inject it) when adding Claude support.
    """
    run_id = ensure_run(request.run_id)
    update_stage(run_id, "reviewer", "running", input_payload={"code": request.code})

    # TODO: inject the provider via dependency injection.
    llm = OpenSourceLLMProvider()
    agent = ReviewerAgent(llm=llm)
    try:
        result = agent.run(code=request.code)
    except Exception as exc:
        update_stage(run_id, "reviewer", "error", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail={"run_id": run_id, "stage": "reviewer", "error": str(exc)},
        ) from exc

    result["run_id"] = run_id
    update_stage(
        run_id,
        "reviewer",
        "success",
        output_payload={"agent": result.get("agent"), "approved": result.get("approved")},
    )
    return ReviewerResponse(**result)
