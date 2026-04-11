"""
HTTP router for the Developer Agent.

Endpoint:  POST /agents/developer
Called by: n8n orchestrator (receives output from Planner Agent)
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from agents.developer.agent import DeveloperAgent
from providers.open_source import OpenSourceLLMProvider

router = APIRouter(prefix="/agents/developer", tags=["Developer"])


class DeveloperRequest(BaseModel):
    """Request body for the Developer endpoint."""

    plan: Any  # Structured plan produced by the PlannerAgent.


class DeveloperResponse(BaseModel):
    """Response body returned by the Developer endpoint."""

    agent: str
    plan: Any
    code: str  # TODO: replace with a structured type once the agent is implemented.


@router.post("", response_model=DeveloperResponse, summary="Run the Developer Agent")
def run_developer(request: DeveloperRequest) -> DeveloperResponse:
    """
    Accepts a development plan and returns generated code artefacts produced
    by the Developer Agent.

    This stub always uses the open-source LLM provider.  Swap the provider
    instance here (or inject it) when adding Claude support.
    """
    # TODO: inject the provider via dependency injection.
    llm = OpenSourceLLMProvider()
    agent = DeveloperAgent(llm=llm)
    result = agent.run(plan=request.plan)
    return DeveloperResponse(**result)
