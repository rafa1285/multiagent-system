"""
Reviewer Agent.

Responsibility: Analyse the code produced by the Developer Agent and return
feedback (bugs, improvements, style issues).

The orchestrator (n8n) calls POST /agents/reviewer with the code as input.
"""

import json
from pathlib import Path
from typing import Any

from providers.base import BaseLLMProvider


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / "system.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return "You are the Reviewer agent. Return an approval decision with findings and concise summary."


class ReviewerAgent:
    """Stub for the Reviewer agent."""

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm
        self.system_prompt = _load_system_prompt()

    def run(self, code: Any) -> dict:
        """
        Receive the *code* artefacts from the Developer and return a review.

        TODO: implement prompt engineering and structured review parsing.

        :param code: Code artefacts produced by the DeveloperAgent.
        :returns: A dict containing review comments and a pass/fail verdict.
        """
        if isinstance(code, str):
            try:
                normalized_code = json.loads(code)
            except json.JSONDecodeError:
                normalized_code = {"raw": code, "artifacts": []}
        else:
            normalized_code = code if isinstance(code, dict) else {"raw": str(code), "artifacts": []}

        prompt = f"{self.system_prompt}\n\nReview the following code: {normalized_code}"
        response = self.llm.complete(prompt=prompt)
        artifacts = normalized_code.get("artifacts") or []
        approved = bool(artifacts) and normalized_code.get("implementation_status") == "implemented"
        findings = [] if approved else ["La implementacion no aporta artefactos suficientes para aprobarla."]
        review_payload = {
            "approved": approved,
            "findings": findings,
            "summary": "Review aprobado" if approved else "Review con cambios requeridos",
            "model_notes": response,
        }
        return {
            "agent": "reviewer",
            "code": normalized_code,
            "review": json.dumps(review_payload, ensure_ascii=True),
            "approved": approved,
        }
