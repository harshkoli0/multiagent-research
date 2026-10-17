#!/bin/sh
# One image, several modes:
#   docker run ... research-studio                 -> Streamlit UI (default)
#   docker run ... research-studio ui              -> Streamlit UI
#   docker run ... research-studio cli "question"  -> one-shot CLI run, prints the article
#   docker run ... research-studio check           -> verifies API keys + Groq model access
#   docker run ... research-studio <any command>   -> runs that command (e.g. sh)
set -e

banner() {
  cat <<'EOF'
  __  __       _ _   _      _                    _
 |  \/  |_   _| | |_(_)    / \   __ _  ___ _ __ | |_
 | |\/| | | | | | __| |   / _ \ / _` |/ _ \ '_ \| __|
 | |  | | |_| | | |_| |  / ___ \ (_| |  __/ | | | |_
 |_|  |_|\__,_|_|\__|_| /_/   \_\__, |\___|_| |_|\__|
            planner -> researcher |___/ -> writer -> reviewer
EOF
}

require_keys() {
  missing=""
  [ -n "$GROQ_API_KEY" ] || missing="$missing GROQ_API_KEY"
  [ -n "$TAVILY_API_KEY" ] || missing="$missing TAVILY_API_KEY"
  if [ -n "$missing" ]; then
    echo "ERROR: missing environment variable(s):$missing" >&2
    echo "Pass them with --env-file .env (or -e NAME=value)." >&2
    exit 1
  fi
}

mode="${1:-ui}"

case "$mode" in
  ui)
    banner
    require_keys
    echo "Model: ${GROQ_MODEL:-openai/gpt-oss-20b}"
    echo "Open http://localhost:${PORT:-8501}"
    exec streamlit run streamlit_app.py --server.port "${PORT:-8501}" --server.address 0.0.0.0
    ;;
  cli)
    shift
    require_keys
    if [ $# -eq 0 ]; then
      echo 'Usage: cli "your research question"' >&2
      exit 2
    fi
    exec python app.py "$@"
    ;;
  check)
    require_keys
    exec python - <<'EOF'
import os
from groq import Groq
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
ids = {m.id for m in Groq().models.list().data}
print(f"GROQ_API_KEY  ok ({len(ids)} models visible)")
print(f"GROQ_MODEL    {model}: {'ok' if model in ids else 'NOT AVAILABLE'}")
print("TAVILY_API_KEY set")
raise SystemExit(0 if model in ids else 1)
EOF
    ;;
  *)
    exec "$@"
    ;;
esac
