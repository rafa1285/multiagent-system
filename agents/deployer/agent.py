"""
Deployer Agent.

Responsibility: Take reviewed, approved code and handle deployment steps
(e.g. writing files to disk, calling CI/CD APIs, or triggering cloud deploys).

The orchestrator (n8n) calls POST /agents/deployer with the reviewed code.
"""

import json
from pathlib import Path
from typing import Any

from providers.base import BaseLLMProvider


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / "system.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return "You are the Deployer agent. Return deployment readiness and traceable steps."


class DeployerAgent:
    """Stub for the Deployer agent."""

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm
        self.system_prompt = _load_system_prompt()

    def run(self, review: Any) -> dict:
        """
        Receive the *review* artefact from the Reviewer and deploy the code.

        TODO: implement actual deployment logic (file writes, API calls, …).

        :param review: Review output produced by the ReviewerAgent.
        :returns: A dict containing the deployment status and any logs.
        """
        if isinstance(review, str):
            try:
                normalized_review = json.loads(review)
            except json.JSONDecodeError:
                normalized_review = {"approved": False, "raw": review}
        else:
            normalized_review = review if isinstance(review, dict) else {"approved": False, "raw": str(review)}

        prompt = f"{self.system_prompt}\n\nGenerate deployment steps for: {normalized_review}"
        response = self.llm.complete(prompt=prompt)
        approved = bool(normalized_review.get("approved"))
        status = "validated" if approved else "blocked"
        deployment_payload = {
            "status": status,
            "ready_for_close": approved,
            "steps": [
                "Revisar estado del pipeline",
                "Confirmar validaciones tecnicas",
                "Autorizar cierre Jira solo con evidencia positiva",
            ],
            "model_notes": response,
        }
        return {
            "agent": "deployer",
            "review": normalized_review,
            "deployment": json.dumps(deployment_payload, ensure_ascii=True),
            "status": status,
        }
