"""
Planner Agent.

Responsibility: Break down a high-level user request into an ordered list of
tasks that the other agents (Developer, Reviewer, Deployer) will execute.

The orchestrator (n8n) calls POST /agents/planner and forwards the result to
the next agent in the pipeline.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml

from providers.base import BaseLLMProvider


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / "system.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return "You are the Planner agent. Return a structured plan with objective, family, subtasks and validation."


def _default_projects_path() -> Path:
    workspace_root = Path(__file__).resolve().parents[3]
    return workspace_root / "orchestrator" / "config" / "projects.yaml"


def _load_projects_map() -> Dict[str, Any]:
    configured = os.getenv("PROJECTS_MAP_PATH", "").strip()
    path = Path(configured).resolve() if configured else _default_projects_path()
    if not path.exists():
        return {"path": str(path), "projects": []}

    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    projects = loaded.get("projects") if isinstance(loaded, dict) else []
    if not isinstance(projects, list):
        projects = []
    return {"path": str(path), "projects": projects}


def _match_projects(task_text: str, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    lowered = task_text.lower()
    matches: List[Dict[str, Any]] = []
    for project in projects:
        name = str(project.get("name", "")).strip()
        if name and name.lower() in lowered:
            matches.append(project)
    return matches


class PlannerAgent:
    """Stub for the Planner agent."""

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm
        self.system_prompt = _load_system_prompt()

    def run(self, task: str) -> dict:
        """
        Receive a high-level *task* description and return a structured plan.

        TODO: implement prompt engineering and structured-output parsing.

        :param task: Natural-language description of what needs to be built.
        :returns: A dict containing the generated plan (steps, priorities, …).
        """
        prompt = f"{self.system_prompt}\n\nCreate a development plan for: {task}"
        response = self.llm.complete(prompt=prompt)
        projects_map = _load_projects_map()
        matched_projects = _match_projects(task, projects_map.get("projects", []))
        lowered = task.lower()
        if any(token in lowered for token in ("auth", "api key", "credencial", "secret", "seguridad")):
            family = "security"
            subtasks = [
                "Inspeccionar la superficie actual y localizar puntos sin proteccion.",
                "Definir la estrategia minima segura de autenticacion o proteccion.",
                "Aplicar el cambio tecnico y endurecer los puntos expuestos.",
                "Agregar comprobaciones de no regresion y evidencias operativas.",
            ]
        elif any(token in lowered for token in ("test", "regresion", "suite", "coverage")):
            family = "quality"
            subtasks = [
                "Inventariar los flujos criticos que deben cubrirse.",
                "Definir la matriz de pruebas y casos de exito y fallo.",
                "Implementar las pruebas y dejar las rutas de ejecucion documentadas.",
                "Verificar que la suite detecta fallos y protege el comportamiento actual.",
            ]
        elif any(token in lowered for token in ("whatsapp", "meta", "audio", "whisper")):
            family = "whatsapp"
            subtasks = [
                "Definir el contrato de entrada y salida del canal WhatsApp.",
                "Integrar el componente externo necesario en el workflow de n8n.",
                "Conectar la nueva rama del flujo con planner y respuesta final.",
                "Verificar el recorrido completo y documentar los puntos de fallo.",
            ]
        elif any(token in lowered for token in ("mcp", "tool", "filesystem", "git server", "exec server", "http server")):
            family = "mcp"
            subtasks = [
                "Definir el contrato de la herramienta y sus limites de seguridad.",
                "Implementar la operacion principal y el aislamiento esperado.",
                "Agregar validaciones de entrada y errores operativos auditables.",
                "Verificar el comportamiento desde el orquestador con evidencia reproducible.",
            ]
        elif any(token in lowered for token in ("db", "database", "postgres", "migracion")):
            family = "data"
            subtasks = [
                "Analizar el estado actual y la compatibilidad con la nueva persistencia.",
                "Definir el plan de cambio y los criterios de no downtime.",
                "Aplicar la configuracion o migracion necesaria con rollback claro.",
                "Validar el estado final y la continuidad operativa del servicio.",
            ]
        else:
            family = "platform"
            subtasks = [
                "Analizar el alcance tecnico y los archivos afectados.",
                "Diseñar el cambio minimo con criterios de aceptacion claros.",
                "Implementar la solucion y revisar riesgos o regresiones.",
                "Verificar el comportamiento final con evidencia antes de cerrar la tarea.",
            ]

        plan_payload = {
            "objective": task,
            "family": family,
            "subtasks": subtasks,
            "project_context": {
                "projects_map_path": projects_map.get("path"),
                "known_projects": [item.get("name") for item in projects_map.get("projects", [])],
                "matched_projects": matched_projects,
            },
            "validation": [
                "La implementacion debe dejar evidencia tecnica verificable.",
                "No se cierra Jira si el flujo principal no responde correctamente.",
                "El reviewer debe dejar veredicto aprobatorio para continuar.",
            ],
            "model_notes": response,
        }
        return {
            "agent": "planner",
            "task": task,
            "plan": json.dumps(plan_payload, ensure_ascii=True),
        }
