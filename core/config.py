"""
Application-wide configuration settings.

Values are read from environment variables so they can be overridden at
deployment time without changing source code.
"""

import os


# ---------------------------------------------------------------------------
# LLM Provider
# ---------------------------------------------------------------------------
# Which LLM provider to use: "ollama" (default, self-hosted), "openai", or "groq".
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")

# Model name passed through to the active provider.
LLM_MODEL: str = os.getenv("LLM_MODEL", "mistral")

# Base URL for a locally-hosted or self-hosted LLM API (e.g. Ollama).
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")

# Timeout in seconds for the active LLM provider HTTP requests.
LLM_HTTP_TIMEOUT: float = float(os.getenv("LLM_HTTP_TIMEOUT", "30"))

# API key – required by cloud providers such as Claude.
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
MULTIAGENT_API_KEY: str = os.getenv("MULTIAGENT_API_KEY", "").strip()

# ---------------------------------------------------------------------------
# Run state persistence
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
RUN_STATE_DATABASE_URL: str = os.getenv("RUN_STATE_DATABASE_URL", DATABASE_URL).strip()
RUN_STATE_SQLITE_PATH: str = os.getenv("RUN_STATE_SQLITE_PATH", "data/run_state.db")
RUN_STAGE_MAX_ATTEMPTS: int = int(os.getenv("RUN_STAGE_MAX_ATTEMPTS", "3"))
PROJECTS_MAP_PATH: str = os.getenv("PROJECTS_MAP_PATH", "").strip()

# ---------------------------------------------------------------------------
# GitHub integration
# ---------------------------------------------------------------------------
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_OWNER: str = os.getenv("GITHUB_OWNER", "").strip()
GITHUB_API_BASE: str = os.getenv("GITHUB_API_BASE", "https://api.github.com").strip().rstrip("/")
GITHUB_CREATE_IN_ORG: bool = os.getenv("GITHUB_CREATE_IN_ORG", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Jira integration
# ---------------------------------------------------------------------------
JIRA_BASE_URL: str = os.getenv("JIRA_BASE_URL", "").strip().rstrip("/")
JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "").strip()
JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "").strip()
JIRA_PROJECT_KEY: str = os.getenv("JIRA_PROJECT_KEY", "MAS").strip()

# ---------------------------------------------------------------------------
# Observability provider
# ---------------------------------------------------------------------------
OBSERVABILITY_PROVIDER: str = os.getenv("OBSERVABILITY_PROVIDER", "supabase").strip().lower()

# Supabase observability
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY", "")).strip()
SUPABASE_SCHEMA: str = os.getenv("SUPABASE_SCHEMA", "").strip()
SUPABASE_LOGS_TABLE: str = os.getenv("SUPABASE_LOGS_TABLE", "app_trace_events").strip()
SUPABASE_HTTP_TIMEOUT: float = float(os.getenv("SUPABASE_HTTP_TIMEOUT", "15"))
SUPABASE_ENABLE_LOG_WRITE: bool = os.getenv("SUPABASE_ENABLE_LOG_WRITE", "false").lower() == "true"
