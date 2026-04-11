"""
Developer Agent.

Responsibility: Generate source code based on the plan produced by the
Planner Agent.

The orchestrator (n8n) calls POST /agents/developer with the plan as input.
"""

from providers.base import BaseLLMProvider


class DeveloperAgent:
    """Stub for the Developer agent."""

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm

    def run(self, plan: dict) -> dict:
        """
        Receive the *plan* from the Planner and return generated code.

        TODO: implement prompt engineering, file scaffolding, and code parsing.

        :param plan: Structured plan produced by the PlannerAgent.
        :returns: A dict containing the generated code artefacts.
        """
        # Stub – call the LLM and return a placeholder code snippet.
        response = self.llm.complete(prompt=f"Implement the following plan: {plan}")
        return {
            "agent": "developer",
            "plan": plan,
            "code": response,
            # TODO: parse LLM output into individual files / code blocks.
        }
