"""
HTTP router for the Planner Agent.

Endpoint:  POST /agents/planner
Called by: n8n orchestrator
"""

from fastapi import APIRouter
from pydantic import BaseModel

from agents.planner.agent import PlannerAgent
from providers.open_source import OpenSourceLLMProvider

router = APIRouter(prefix="/agents/planner", tags=["Planner"])


class PlannerRequest(BaseModel):
    """Request body for the Planner endpoint."""

    task: str  # High-level description of what needs to be built.


class PlannerResponse(BaseModel):
    """Response body returned by the Planner endpoint."""

    agent: str
    task: str
    plan: str  # TODO: replace with a structured type once the agent is implemented.


@router.post("", response_model=PlannerResponse, summary="Run the Planner Agent")
def run_planner(request: PlannerRequest) -> PlannerResponse:
    """
    Accepts a high-level task description and returns a structured development
    plan produced by the Planner Agent.

    This stub always uses the open-source LLM provider.  Swap the provider
    instance here (or inject it) when adding Claude support.
    """
    # TODO: inject the provider via dependency injection.
    llm = OpenSourceLLMProvider()
    agent = PlannerAgent(llm=llm)
    result = agent.run(task=request.task)
    return PlannerResponse(**result)
