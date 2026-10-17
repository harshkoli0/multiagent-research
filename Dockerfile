# syntax=docker/dockerfile:1.7
# ---------------------------------------------------------------------------
# Multi-Agent Research Studio
#   Stage 1 (builder): resolves dependencies from pyproject.toml with uv into
#                      an isolated virtualenv, using a BuildKit cache mount.
#   Stage 2 (runtime): slim image with only the venv + source, runs as a
#                      non-root user, self-heals via a Streamlit health check.
# ---------------------------------------------------------------------------

ARG PYTHON_VERSION=3.12

# ---------- Stage 1: build the virtualenv ----------
FROM python:${PYTHON_VERSION}-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/opt/venv

WORKDIR /build
COPY pyproject.toml ./

# Only pyproject.toml is copied first, so code edits don't trigger a dependency reinstall
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /opt/venv && \
    uv pip install -r pyproject.toml


# ---------- Stage 2: runtime ----------
FROM python:${PYTHON_VERSION}-slim AS runtime

LABEL org.opencontainers.image.title="Multi-Agent Research Studio" \
      org.opencontainers.image.description="Planner, researcher, writer and reviewer agents (LangGraph + Groq + Tavily) with a Streamlit UI" \
      org.opencontainers.image.source="https://github.com/harshkoli0/multi_agents"

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501 \
    GROQ_MODEL=openai/gpt-oss-20b \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Unprivileged user: the app never needs root
RUN groupadd --system agents && useradd --system --gid agents --create-home agent

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=agent:agents . .

# Strip Windows CRLF line endings (repo is edited on Windows) and make the entrypoint executable
RUN sed -i 's/\r$//' docker/entrypoint.sh && chmod +x docker/entrypoint.sh

USER agent
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",\"8501\")}/_stcore/health', timeout=4)" || exit 1

ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["ui"]
