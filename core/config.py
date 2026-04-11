"""
Application-wide configuration settings.

Values are read from environment variables so they can be overridden at
deployment time without changing source code.
"""

import os


# ---------------------------------------------------------------------------
# LLM Provider
# ---------------------------------------------------------------------------
# Which LLM provider to use.  Currently only "open_source" is implemented;
# set to "claude" when the Anthropic integration is added.
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "open_source")

# Model name passed through to the active provider.
LLM_MODEL: str = os.getenv("LLM_MODEL", "mistral")

# Base URL for a locally-hosted or self-hosted LLM API (e.g. Ollama).
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")

# API key – required by cloud providers such as Claude.
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
