"""
HTTP router for the Reviewer Agent.

Endpoint:  POST /agents/reviewer
Called by: n8n orchestrator (receives output from Developer Agent)
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from agents.reviewer.agent import ReviewerAgent
from core.auth import require_api_key
from core.run_state import StageRetryLimitExceededError, finish_stage_error, finish_stage_success, set_run_status, start_stage
from providers.open_source import OpenSourceLLMProvider

router = APIRouter(prefix="/agents/reviewer", tags=["Reviewer"], dependencies=[Depends(require_api_key)])


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
    try:
        attempt = start_stage(request.run_id, "reviewer", {"code": request.code})
    except StageRetryLimitExceededError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if attempt["cached"]:
        cached = attempt["output_payload"]
        return ReviewerResponse(**cached)

    run_id = attempt["run_id"]

    # TODO: inject the provider via dependency injection.
    llm = OpenSourceLLMProvider()
    agent = ReviewerAgent(llm=llm)
    try:
        result = agent.run(code=request.code)
    except Exception as exc:
        finish_stage_error(run_id, "reviewer", attempt["attempt_id"], str(exc))
        raise HTTPException(
            status_code=500,
            detail={"run_id": run_id, "stage": "reviewer", "error": str(exc)},
        ) from exc

    result["run_id"] = run_id
    finish_stage_success(run_id, "reviewer", attempt["attempt_id"], result)
    if not result.get("approved"):
        set_run_status(run_id, "changes_required", current_stage="reviewer")
    return ReviewerResponse(**result)
