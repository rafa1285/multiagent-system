"""
HTTP router for the Reviewer Agent.

Endpoint:  POST /agents/reviewer
Called by: n8n orchestrator (receives output from Developer Agent)
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from agents.reviewer.agent import ReviewerAgent
from providers.open_source import OpenSourceLLMProvider

router = APIRouter(prefix="/agents/reviewer", tags=["Reviewer"])


class ReviewerRequest(BaseModel):
    """Request body for the Reviewer endpoint."""

    code: Any  # Code artefacts produced by the DeveloperAgent.


class ReviewerResponse(BaseModel):
    """Response body returned by the Reviewer endpoint."""

    agent: str
    code: Any
    review: str  # TODO: replace with a structured type once the agent is implemented.
    approved: bool


@router.post("", response_model=ReviewerResponse, summary="Run the Reviewer Agent")
def run_reviewer(request: ReviewerRequest) -> ReviewerResponse:
    """
    Accepts generated code artefacts and returns a code review with a
    pass/fail verdict produced by the Reviewer Agent.

    This stub always uses the open-source LLM provider.  Swap the provider
    instance here (or inject it) when adding Claude support.
    """
    # TODO: inject the provider via dependency injection.
    llm = OpenSourceLLMProvider()
    agent = ReviewerAgent(llm=llm)
    result = agent.run(code=request.code)
    return ReviewerResponse(**result)
