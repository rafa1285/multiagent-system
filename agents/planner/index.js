// Planner Agent - Entry point
// The run() function will be implemented by Copilot based on schema.json and prompts/base.md

async function run(input) {
  // Copilot will implement this
  return {};
}

module.exports = { run };

/*
You are the PLANNER agent inside a multi-agent MCP system.

Your job is to implement the logic of this agent based on:

- the schema.json in this folder
- the prompts/base.md in this folder
- the backend-template repository
- the orchestrator flows
- the agent-tools utilities

RULES:
- Do NOT invent new folders or files.
- Do NOT modify other agents.
- Do NOT modify MCP configuration.
- Only implement the logic for this agent inside index.js.
- Read schema.json to understand input/output.
- Read prompts/base.md to understand the agent's role.
- Keep the implementation modular.
- Export a single async function called `run`.
- The function receives an object matching the schema input.
- The function returns an object matching the schema output.

Start by generating a minimal but functional implementation.
*/

// implement run()
async function run(input) {
  const description = input?.description || "No description provided";

  // Generate a structured plan based on the description
  const plan = {
    summary: `Plan generado a partir de la descripción: "${description}"`,
    tasks: [
      {
        id: "task-1",
        title: "Analizar la descripción",
        details: "Comprender el objetivo general, restricciones y alcance."
      },
      {
        id: "task-2",
        title: "Identificar componentes necesarios",
        details: "Determinar módulos, endpoints, modelos o funciones requeridas."
      },
      {
        id: "task-3",
        title: "Descomponer en subtareas",
        details: "Crear pasos concretos y ordenados para el Developer."
      }
    ]
  };

  return { plan };
}
