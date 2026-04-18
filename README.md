# multiagent-system

Multi-agent backend system orchestrated by **n8n**, designed to automatically
plan, develop, review, and deploy backend projects through a chain of
specialised AI agents.

---

## Purpose

This repository contains the multi-agent logic and HTTP endpoints that n8n
calls as part of a larger automation pipeline.  Each agent is a standalone
FastAPI endpoint; n8n wires them together by forwarding each agent's output to
the next one in the chain.

```
n8n  →  POST /agents/planner
     →  POST /agents/developer
     →  POST /agents/reviewer
     →  POST /agents/deployer
```

---

## Agents

| Agent | Endpoint | Responsibility |
|-------|----------|----------------|
| **Planner** | `POST /agents/planner` | Breaks a high-level task into an ordered development plan |
| **Developer** | `POST /agents/developer` | Generates source code from the plan |
| **Reviewer** | `POST /agents/reviewer` | Reviews the generated code and returns feedback |
| **Deployer** | `POST /agents/deployer` | Deploys approved code (file writes, CI/CD calls, etc.) |

---

## Project Structure

```
multiagent-system/
├── main.py                         # FastAPI app – registers all routers
├── requirements.txt
│
├── agents/                         # One sub-package per agent
│   ├── planner/
│   │   ├── agent.py                # Agent logic (stub)
│   │   └── router.py               # FastAPI router / HTTP endpoint
│   ├── developer/
│   │   ├── agent.py
│   │   └── router.py
│   ├── reviewer/
│   │   ├── agent.py
│   │   └── router.py
│   └── deployer/
│       ├── agent.py
│       └── router.py
│
├── providers/                      # LLM provider abstraction layer
│   ├── base.py                     # Abstract interface (BaseLLMProvider)
│   └── open_source.py              # Open-source / self-hosted model stub
│
└── core/
  ├── config.py                   # App-wide settings (env-var driven)
  └── run_state.py                # In-memory run tracking state machine
```

---

## LLM Provider Abstraction

All agents receive an `llm` object that implements `BaseLLMProvider`
(`providers/base.py`).  This makes it trivial to swap the underlying model:

* **Now** – `OpenSourceLLMProvider` in `providers/open_source.py` (targets a
  self-hosted model, e.g. via [Ollama](https://ollama.com/)).
* **Later** – add `providers/claude.py` implementing the same interface and
  change `LLM_PROVIDER=claude` in your environment.

---

## Getting Started

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) configure via environment variables
export LLM_PROVIDER=open_source
export LLM_MODEL=mistral
export LLM_BASE_URL=http://localhost:11434

# 3. Start the server
uvicorn main:app --reload
```

Interactive API docs: http://localhost:8000/docs

---

## Deploy on Render

This repository includes a Render Blueprint file:

- `render.yaml`

### Quick deploy

1. In Render, create a new Blueprint service from your repo.
2. Set Root Directory to `multiagent-system` if Render asks for it.
3. Apply the Blueprint and deploy.
4. Confirm health endpoint:
  - `GET /`
5. Confirm docs endpoint:
  - `GET /docs`

### Use this URL in n8n

After deploy, copy the public URL of this service and set it as:

- `MULTIAGENT_API_BASE_URL`

Where to set it:

1. Render Environment for the `n8n-service`
2. Local file for MCP diagnostics:
  - `orchestrator/config/n8n-mcp.env`

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `open_source` | Active LLM provider (`open_source` \| `claude`) |
| `LLM_MODEL` | `mistral` | Model name forwarded to the provider |
| `LLM_BASE_URL` | `http://localhost:11434` | Base URL for a self-hosted LLM API |
| `LLM_API_KEY` | _(empty)_ | API key for cloud providers (e.g. Claude) |
| `HOST` | `0.0.0.0` | Bind address for the HTTP server |
| `PORT` | `8000` | Port for the HTTP server |

Local template:

- `.env.example`

---

## Run Tracking (run_id)

All agent endpoints now accept an optional `run_id` and include it in their
responses. If omitted, the backend creates one automatically.

State endpoints:

- `POST /runs` creates a new run id
- `GET /runs/{run_id}` returns per-stage status and event history
- `GET /runs?limit=20` lists recent runs

Per-stage lifecycle tracked by the API:

- `running`
- `success`
- `error`

When the `deployer` stage succeeds, the run status transitions to `completed`.

---

## Roadmap

- [ ] Implement real LLM calls in `providers/open_source.py`
- [ ] Add `providers/claude.py` for Anthropic Claude support
- [ ] Flesh out agent logic with proper prompt engineering
- [ ] Add structured output parsing in each agent
- [ ] Add authentication / API-key validation on all endpoints
- [ ] Containerise with Docker

Sistema multiagente orquestado por n8n, con agentes y MCP, para generar y desplegar proyectos backend.

## Estructura del repositorio

### agents/
Contiene los agentes principales del sistema, cada uno con una responsabilidad clara dentro del flujo multiagente:

- *planner/*  
  Genera planes y tareas que definen qué debe hacerse.

- *developer/*  
  Implementa el código necesario según los planes generados.

- *reviewer/*  
  Revisa el código generado para asegurar calidad y consistencia.

- *deployer/*  
  Gestiona el despliegue del proyecto backend generado.

### common/
Utilidades y módulos compartidos entre los agentes.  
Actualmente vacío, se irá completando conforme evolucione el sistema.

### config/
Archivos de configuración inicial y placeholders.  
No contiene valores reales todavía; se completará en fases posteriores.
