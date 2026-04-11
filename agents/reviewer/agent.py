"""
Reviewer Agent.

Responsibility: Analyse the code produced by the Developer Agent and return
feedback (bugs, improvements, style issues).

The orchestrator (n8n) calls POST /agents/reviewer with the code as input.
"""

from providers.base import BaseLLMProvider


class ReviewerAgent:
    """Stub for the Reviewer agent."""

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm

    def run(self, code: dict) -> dict:
        """
        Receive the *code* artefacts from the Developer and return a review.

        TODO: implement prompt engineering and structured review parsing.

        :param code: Code artefacts produced by the DeveloperAgent.
        :returns: A dict containing review comments and a pass/fail verdict.
        """
        # Stub – call the LLM and return a placeholder review.
        response = self.llm.complete(prompt=f"Review the following code: {code}")
        return {
            "agent": "reviewer",
            "code": code,
            "review": response,
            "approved": False,  # TODO: derive from LLM output.
        }
