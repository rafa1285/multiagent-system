"""
Planner Agent.

Responsibility: Break down a high-level user request into an ordered list of
tasks that the other agents (Developer, Reviewer, Deployer) will execute.

The orchestrator (n8n) calls POST /agents/planner and forwards the result to
the next agent in the pipeline.
"""

from providers.base import BaseLLMProvider


class PlannerAgent:
    """Stub for the Planner agent."""

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm

    def run(self, task: str) -> dict:
        """
        Receive a high-level *task* description and return a structured plan.

        TODO: implement prompt engineering and structured-output parsing.

        :param task: Natural-language description of what needs to be built.
        :returns: A dict containing the generated plan (steps, priorities, …).
        """
        # Stub – call the LLM and return a placeholder plan.
        response = self.llm.complete(prompt=f"Create a development plan for: {task}")
        return {
            "agent": "planner",
            "task": task,
            "plan": response,
            # TODO: parse LLM output into structured steps.
        }
