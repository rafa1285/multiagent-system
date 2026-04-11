"""
HTTP router for the Deployer Agent.

Endpoint:  POST /agents/deployer
Called by: n8n orchestrator (receives output from Reviewer Agent)
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from agents.deployer.agent import DeployerAgent
from providers.open_source import OpenSourceLLMProvider

router = APIRouter(prefix="/agents/deployer", tags=["Deployer"])


class DeployerRequest(BaseModel):
    """Request body for the Deployer endpoint."""

    review: Any  # Review output produced by the ReviewerAgent.


class DeployerResponse(BaseModel):
    """Response body returned by the Deployer endpoint."""

    agent: str
    review: Any
    deployment: str  # TODO: replace with a structured type once the agent is implemented.
    status: str


@router.post("", response_model=DeployerResponse, summary="Run the Deployer Agent")
def run_deployer(request: DeployerRequest) -> DeployerResponse:
    """
    Accepts a code review and triggers deployment steps, returning the
    deployment status produced by the Deployer Agent.

    This stub always uses the open-source LLM provider.  Swap the provider
    instance here (or inject it) when adding Claude support.
    """
    # TODO: inject the provider via dependency injection.
    llm = OpenSourceLLMProvider()
    agent = DeployerAgent(llm=llm)
    result = agent.run(review=request.review)
    return DeployerResponse(**result)
