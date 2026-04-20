"""
Developer Agent.

Responsibility: Generate source code based on the plan produced by the
Planner Agent.

The orchestrator (n8n) calls POST /agents/developer with the plan as input.
"""

import json
from pathlib import Path
from typing import Any

from providers.base import BaseLLMProvider


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / "system.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return "You are the Developer agent. Produce implementation artifacts as structured JSON-compatible content."


class DeveloperAgent:
    """Stub for the Developer agent."""

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm
        self.system_prompt = _load_system_prompt()

    def run(self, plan: Any) -> dict:
        """
        Receive the *plan* from the Planner and return generated code.

        TODO: implement prompt engineering, file scaffolding, and code parsing.

        :param plan: Structured plan produced by the PlannerAgent.
        :returns: A dict containing the generated code artefacts.
        """
        if isinstance(plan, str):
            try:
                normalized_plan = json.loads(plan)
            except json.JSONDecodeError:
                normalized_plan = {"objective": plan, "subtasks": [plan]}
        else:
            normalized_plan = plan if isinstance(plan, dict) else {"objective": str(plan), "subtasks": [str(plan)]}

        prompt = f"{self.system_prompt}\n\nImplement the following plan: {normalized_plan}"
        response = self.llm.complete(prompt=prompt)
        subtasks = normalized_plan.get("subtasks") or []
        artifacts = []
        for index, subtask in enumerate(subtasks, start=1):
            artifacts.append(
                {
                    "name": f"artifact_{index}",
                    "type": "implementation_note",
                    "summary": str(subtask),
                }
            )

        code_payload = {
            "objective": normalized_plan.get("objective"),
            "family": normalized_plan.get("family", "platform"),
            "completed_subtasks": [str(item) for item in subtasks],
            "artifacts": artifacts,
            "implementation_status": "implemented",
            "model_notes": response,
        }
        return {
            "agent": "developer",
            "plan": normalized_plan,
            "code": json.dumps(code_payload, ensure_ascii=True),
        }
