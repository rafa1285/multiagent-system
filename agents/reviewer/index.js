// Reviewer Agent - Entry point
// This agent revisa los archivos generados por el Developer y devuelve
// un informe de calidad siguiendo el schema.json.

async function run(input) {
  const files = input?.files;

  if (!files || !Array.isArray(files)) {
    return {
      approved: false,
      issues: ["No files provided to reviewer agent."]
    };
  }

  // Minimal review: detect empty or missing content
  const issues = [];

  files.forEach(file => {
    if (!file.content || file.content.trim().length === 0) {
      issues.push(`El archivo ${file.path} está vacío o no contiene contenido válido.`);
    }
  });

  const approved = issues.length === 0;

  return {
    approved,
    issues
  };
}

module.exports = { run };

/*
You are the REVIEWER agent inside a multi-agent MCP system.

Your job is to implement the logic of this agent based on:

- the schema.json in this folder
- the prompts/base.md in this folder
- the backend-template repository
- the orchestrator flows
- the agent-tools utilities

RULES:
- Do NOT invent new fields or structures.
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
