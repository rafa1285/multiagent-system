// This file is responsible for the Developer agent, which is designed to assist in the development process and ensure code quality.
// Developer Agent - Entry point
// The run() function will be implemented based on schema.json and prompts/base.md

async function run(input) {
  const plan = input?.plan;

  if (!plan) {
    return {
      files: [],
      error: "No plan provided to developer agent."
    };
  }

  // Convert each task into a minimal code file
  const files = plan.tasks.map((task, index) => {
    const safeId = task.id || `task-${index + 1}`;
    const fileName = `${safeId}.js`;

    const content =
`/**
 * ${task.title}
 * ${task.details || ""}
 * Generado automáticamente por el Developer agent.
 */

function ${safeId.replace(/[^a-zA-Z0-9]/g, "_")}() {
  // TODO: implementar lógica real basada en el plan
  console.log("Ejecutando ${task.title}");
}

module.exports = ${safeId.replace(/[^a-zA-Z0-9]/g, "_")};
`;

    return {
      path: `generated/${fileName}`,
      content
    };
  });

  return { files };
}

module.exports = { run };

/*
You are the DEVELOPER agent inside a multi-agent MCP system.

Your job is to implement the logic of this agent based on:

- the schema.json in this folder
- the prompts/base.md in this folder
- the backend-template repository
- the orchestrator flows
- the agent-tools utilities

RULES:
- Do NOT invent new folders or files outside the generated/ directory.
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