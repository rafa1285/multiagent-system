# multiagent-system

Multi-agent system orchestrated by n8n. Each agent exposes an HTTP endpoint that n8n calls in sequence to plan, develop, review, and deploy backend projects.

## Structure

```
multiagent-system/
├── planner/          # Breaks a high-level task into an ordered execution plan
│   └── index.js
├── developer/        # Generates source code / config files for each sub-task
│   └── index.js
├── reviewer/         # Reviews generated code and returns a pass/fail report
│   └── index.js
├── deployer/         # Deploys approved artifacts to the target environment
│   └── index.js
├── common/           # Shared utilities (empty – to be filled during implementation)
└── config/
    └── config.js     # Central configuration placeholder (API keys, URLs, etc.)
```

## Agent responsibilities

| Agent | Role |
|-------|------|
| **planner** | Receives a task from n8n and returns a structured list of sub-tasks |
| **developer** | Receives a sub-task and produces the corresponding code artifacts |
| **reviewer** | Analyses code artifacts and reports quality / security issues |
| **deployer** | Takes approved artifacts and runs the deployment pipeline |
