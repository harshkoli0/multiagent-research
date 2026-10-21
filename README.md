# Multi-Agent Research Studio

A team of four LLM agents that turns a question into a researched, cited article. It is built with [LangGraph](https://github.com/langchain-ai/langgraph), [Groq](https://groq.com) and [Tavily](https://tavily.com), and comes with a Streamlit UI and a CLI.

```
query ─▶ 🧭 Planner ─▶ 🔎 Researcher ─▶ ✍️ Writer ─▶ 🧐 Reviewer ─▶ final article
```

| Agent | What it does |
|-------|--------------|
| **Planner** (`agent/planner.py`) | Produces a structured plan: objective, audience, 3-6 key aspects and 3-5 targeted search queries |
| **Researcher** (`agent/researcher.py`) | Runs all search queries in parallel through Tavily, removes duplicate sources by URL and writes research notes with inline `[n]` citations |
| **Writer** (`agent/writer.py`) | Turns the research notes into a detailed article |
| **Reviewer** (`agent/Reviewer.py`) | Polishes grammar, clarity and formatting |

The agents are connected as a linear `StateGraph` in `graph/workflow.py`.

## Requirements

- Python 3.12+
- A [Groq API key](https://console.groq.com/keys)
- A [Tavily API key](https://app.tavily.com)

## Setup

```bash
python -m venv myenv
# Windows
myenv\Scripts\activate
# macOS / Linux
source myenv/bin/activate

# with uv (reads dependencies straight from pyproject.toml)
uv pip install -r pyproject.toml
# or with plain pip
pip install "langchain-core>=1.3" "langchain-groq>=1.1" "langgraph>=1.1" "pydantic>=2.13"   "python-dotenv>=1.2" "rich>=15.0" "streamlit>=1.66" "tavily-python>=0.7"
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your-groq-key
TAVILY_API_KEY=your-tavily-key
# Optional: default model (openai/gpt-oss-20b if unset)
GROQ_MODEL=openai/gpt-oss-20b
```

`.env` and `.streamlit/secrets.toml` are git-ignored, so keys are never committed.

## Usage

### Streamlit UI

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501. From the sidebar you can pick any Groq model available to your key. The UI shows each agent's progress and the sources it used, and lets you download the final article.

### CLI

```bash
python app.py "How are solid-state batteries changing EVs?"
```

If you leave out the question, the CLI prompts for it. It prints the plan, the research notes and the final article.

## Docker

The image is a multi-stage build: dependencies are installed with `uv`, and the app runs as a non-root user with a Streamlit health check.

```bash
# Streamlit UI on http://localhost:8501
docker compose up --build

# One-shot CLI run
docker compose run --rm cli "your research question"

# Check that the API keys work and the model is available
docker compose run --rm check
```

All three services read their keys from `.env`. The UI container runs with a read-only filesystem, all Linux capabilities dropped and `no-new-privileges` set.

## Project structure

```
agent/            planner, researcher, writer and reviewer agents
graph/workflow.py LangGraph state and graph (build_app)
tools/            Tavily web search wrapper
streamlit_app.py  Streamlit UI
app.py            CLI entry point
docker/           container entrypoint (ui | cli | check modes)
.streamlit/       Streamlit theme and server config
```

## Troubleshooting

**`ImportError: cannot import name 'StateGraph' from 'langgraph.graph' (unknown location)`**, or `ModuleNotFoundError` for a package you know you installed.
A pip install was interrupted and left a package half-written. Look in `myenv/Lib/site-packages` for folders whose names start with `~`, or for a package folder with no matching `.dist-info`. Delete those folders and reinstall the dependencies as described in [Setup](#setup).

This happens more often when the project is inside a OneDrive or other synced folder, because the sync client can lock files while pip writes them. If it keeps happening, pause syncing during installs or create the virtualenv outside the synced folder.
