import html
import os
import time
from datetime import datetime
from urllib.parse import urlparse

import streamlit as st
from dotenv import load_dotenv

from graph.workflow import DEFAULT_MODEL, build_app

load_dotenv()

# On Streamlit Cloud the keys live in st.secrets; mirror them into the environment the agents read from
try:
    for _key in ("GROQ_API_KEY", "TAVILY_API_KEY"):
        if _key in st.secrets and not os.getenv(_key):
            os.environ[_key] = str(st.secrets[_key])
except Exception:
    pass  # no secrets.toml locally

st.set_page_config(page_title="Multi-Agent Research Studio", page_icon="🧠", layout="wide")

AGENTS = [
    ("planner", "🧭", "Planner", "Breaks the query into aspects & search queries"),
    ("research", "🔎", "Researcher", "Searches the web in parallel & takes cited notes"),
    ("writer", "✍️", "Writer", "Turns the research into a detailed article"),
    ("reviewer", "🧐", "Reviewer", "Polishes grammar, clarity & formatting"),
]

EXAMPLES = [
    "Benefits of solar energy for homes",
    "How do AI agents use tools?",
    "State of quantum computing in 2026",
    "Is intermittent fasting backed by science?",
]

FALLBACK_MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');

:root {
  --accent: #7c5cff;
  --accent-2: #22d3ee;
  --ok: #34d399;
  --err: #f87171;
  --card: rgba(255,255,255,0.04);
  --border: rgba(255,255,255,0.09);
  --muted: #9aa3b5;
}
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 2rem; max-width: 1200px; }

.hero {
  position: relative; overflow: hidden;
  padding: 2.2rem 2.4rem; border-radius: 22px; margin-bottom: 1.6rem;
  background:
    radial-gradient(circle at 15% 20%, rgba(124,92,255,0.35), transparent 45%),
    radial-gradient(circle at 85% 80%, rgba(34,211,238,0.25), transparent 45%),
    #0f1220;
  border: 1px solid var(--border);
}
.hero h1 {
  font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; margin: 0; line-height: 1.1;
  background: linear-gradient(90deg, #fff, #c7b8ff 50%, var(--accent-2));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { color: var(--muted); margin: .6rem 0 0; font-size: 1.05rem; }
.hero .badge {
  display: inline-block; font-size: .72rem; letter-spacing: .12em; text-transform: uppercase;
  padding: .3rem .7rem; border-radius: 999px; margin-bottom: .9rem;
  border: 1px solid rgba(124,92,255,.5); color: #c7b8ff; background: rgba(124,92,255,.12);
}

.pipeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: .9rem; margin: 1rem 0 1.6rem; }
@media (max-width: 900px) { .pipeline { grid-template-columns: repeat(2, 1fr); } }
.agent {
  position: relative; padding: 1rem 1.1rem; border-radius: 16px;
  background: var(--card); border: 1px solid var(--border); transition: all .3s ease;
}
.agent .icon { font-size: 1.6rem; }
.agent .name { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.05rem; margin-top: .3rem; }
.agent .desc { color: var(--muted); font-size: .8rem; margin-top: .2rem; min-height: 2.2em; }
.agent .status { font-size: .75rem; font-weight: 600; margin-top: .7rem; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); }
.agent.running { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent), 0 0 28px rgba(124,92,255,.35); }
.agent.running .status { color: #c7b8ff; }
.agent.running .status::before {
  content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent); margin-right: 6px; animation: pulse 1s infinite ease-in-out;
}
.agent.done { border-color: rgba(52,211,153,.45); }
.agent.done .status { color: var(--ok); }
.agent.error { border-color: rgba(248,113,113,.6); }
.agent.error .status { color: var(--err); }
@keyframes pulse { 0%,100% { opacity: .3; transform: scale(.8); } 50% { opacity: 1; transform: scale(1.2); } }

.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .9rem; margin-bottom: 1.2rem; }
.stat { padding: .9rem 1.1rem; border-radius: 14px; background: var(--card); border: 1px solid var(--border); }
.stat .v { font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; }
.stat .l { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; }

.src { display: flex; gap: .9rem; padding: .9rem 1rem; border-radius: 14px; margin-bottom: .7rem;
  background: var(--card); border: 1px solid var(--border); }
.src .num { flex: none; width: 2rem; height: 2rem; border-radius: 10px; display: grid; place-items: center;
  font-weight: 700; background: rgba(124,92,255,.18); color: #c7b8ff; }
.src a { color: #e7e9ee; font-weight: 600; text-decoration: none; }
.src a:hover { color: var(--accent-2); }
.src .dom { color: var(--accent-2); font-size: .78rem; margin: .15rem 0 .3rem; }
.src .snip { color: var(--muted); font-size: .85rem; line-height: 1.45; }

.chip { display: inline-block; padding: .25rem .65rem; margin: 0 .4rem .4rem 0; border-radius: 999px;
  font-size: .8rem; background: rgba(34,211,238,.1); border: 1px solid rgba(34,211,238,.3); color: #a5f3fc; }

.article { padding: 1.6rem 2rem; border-radius: 18px; background: var(--card); border: 1px solid var(--border); }
</style>
"""


@st.cache_data(ttl=3600, show_spinner=False)
def available_models():
    try:
        from groq import Groq
        skip = ("whisper", "guard", "orpheus", "safeguard", "allam")
        models = sorted(m.id for m in Groq().models.list().data if not any(s in m.id for s in skip))
        return models or FALLBACK_MODELS
    except Exception:
        return FALLBACK_MODELS


@st.cache_resource(show_spinner=False)
def get_graph(model):
    return build_app(model)


def render_pipeline(placeholder, status, timings):
    cards = []
    for key, icon, name, desc in AGENTS:
        state = status.get(key, "waiting")
        label = {
            "waiting": "Waiting",
            "running": "Working…",
            "done": f"Done · {timings.get(key, 0):.1f}s",
            "error": "Failed",
        }[state]
        cards.append(
            f'<div class="agent {state}"><div class="icon">{icon}</div><div class="name">{name}</div>'
            f'<div class="desc">{desc}</div><div class="status">{label}</div></div>'
        )
    placeholder.markdown(f'<div class="pipeline">{"".join(cards)}</div>', unsafe_allow_html=True)


def run_pipeline(query, model, placeholder):
    graph = get_graph(model)
    status, timings, state = {"planner": "running"}, {}, {"query": query}
    render_pipeline(placeholder, status, timings)

    order = [a[0] for a in AGENTS]
    started = time.perf_counter()
    step_start = started
    current = "planner"
    try:
        for update in graph.stream({"query": query}, stream_mode="updates"):
            for node, values in update.items():
                state.update(values)
                now = time.perf_counter()
                timings[node] = now - step_start
                step_start = now
                status[node] = "done"
                idx = order.index(node)
                if idx + 1 < len(order):
                    current = order[idx + 1]
                    status[current] = "running"
                render_pipeline(placeholder, status, timings)
    except Exception as e:
        status[current] = "error"
        render_pipeline(placeholder, status, timings)
        raise RuntimeError(f"{current} agent failed: {e}") from e

    state["elapsed"] = time.perf_counter() - started
    state["model"] = model
    state["timings"] = timings
    state["at"] = datetime.now().strftime("%H:%M")
    return state


def to_markdown(r):
    sources = "\n".join(f"{i}. [{s['title']}]({s['url']})" for i, s in enumerate(r.get("sources", []), 1))
    return f"# {r['query']}\n\n{r.get('final', '')}\n\n---\n\n## Sources\n\n{sources}\n"


def render_results(r):
    sources = r.get("sources", [])
    words = len(r.get("final", "").split())
    st.markdown(
        f"""<div class="stats">
          <div class="stat"><div class="v">{r['elapsed']:.1f}s</div><div class="l">Total time</div></div>
          <div class="stat"><div class="v">{len(r.get('search_queries', []))}</div><div class="l">Searches</div></div>
          <div class="stat"><div class="v">{len(sources)}</div><div class="l">Sources</div></div>
          <div class="stat"><div class="v">{words:,}</div><div class="l">Words</div></div>
        </div>""",
        unsafe_allow_html=True,
    )

    tab_final, tab_plan, tab_src, tab_notes, tab_draft = st.tabs(
        ["📄 Final article", "🧭 Plan", f"🔗 Sources ({len(sources)})", "🗒️ Research notes", "📝 Draft"]
    )
    with tab_final:
        st.download_button(
            "⬇️ Download as Markdown", to_markdown(r),
            file_name=f"{r['query'][:40].strip().replace(' ', '_')}.md", mime="text/markdown",
        )
        with st.container(border=True):
            st.markdown(r.get("final", ""))
    with tab_plan:
        chips = "".join(f'<span class="chip">🔎 {html.escape(q)}</span>' for q in r.get("search_queries", []))
        st.markdown(f"**Search queries**<br>{chips}", unsafe_allow_html=True)
        st.code(r.get("plan", ""), language=None, wrap_lines=True)
    with tab_src:
        if not sources:
            st.info("No web sources were found for this query.")
        for i, s in enumerate(sources, 1):
            domain = urlparse(s["url"]).netloc.removeprefix("www.")
            snippet = html.escape(s.get("content", "")[:260]) + "…"
            st.markdown(
                f'<div class="src"><div class="num">{i}</div><div>'
                f'<a href="{html.escape(s["url"])}" target="_blank">{html.escape(s["title"] or domain)}</a>'
                f'<div class="dom">{html.escape(domain)}</div><div class="snip">{snippet}</div></div></div>',
                unsafe_allow_html=True,
            )
    with tab_notes:
        st.markdown(r.get("research", ""))
    with tab_draft:
        st.markdown(r.get("draft", ""))


# ---------- Page ----------
st.markdown(CSS, unsafe_allow_html=True)

st.session_state.setdefault("history", [])
st.session_state.setdefault("query", "")

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    models = available_models()
    model = st.selectbox("Groq model", models, index=models.index(DEFAULT_MODEL) if DEFAULT_MODEL in models else 0)

    st.markdown("### 🔑 API keys")
    for key in ("GROQ_API_KEY", "TAVILY_API_KEY"):
        st.markdown(f"{'🟢' if os.getenv(key) else '🔴'} `{key}`")

    st.markdown("### 🕘 History")
    if not st.session_state.history:
        st.caption("Your research runs will appear here.")
    for i, h in enumerate(reversed(st.session_state.history)):
        if st.button(f"{h['at']} · {h['query'][:32]}", key=f"hist{i}", use_container_width=True):
            st.session_state.current = h

st.markdown(
    """<div class="hero">
      <span class="badge">LangGraph · Groq · Tavily</span>
      <h1>Multi-Agent Research Studio</h1>
      <p>Four AI agents plan, research, write and review a cited article on any topic. You can watch each one as it works.</p>
    </div>""",
    unsafe_allow_html=True,
)

cols = st.columns(len(EXAMPLES))
for col, ex in zip(cols, EXAMPLES):
    if col.button(ex, use_container_width=True):
        st.session_state.query = ex

with st.form("ask", border=False):
    query = st.text_area(
        "What should the agents research?", key="query", height=90,
        placeholder="e.g. What are the trade-offs between solar and wind power for small businesses?",
    )
    go = st.form_submit_button("🚀 Run research team", type="primary", use_container_width=True)

pipeline = st.empty()

if go:
    if not query.strip():
        st.warning("Type a question first.")
    elif not (os.getenv("GROQ_API_KEY") and os.getenv("TAVILY_API_KEY")):
        st.error("GROQ_API_KEY and TAVILY_API_KEY must both be set.")
    else:
        try:
            result = run_pipeline(query.strip(), model, pipeline)
            st.session_state.history.append(result)
            st.session_state.current = result
            st.toast(f"Done in {result['elapsed']:.1f}s", icon="✅")
        except Exception as e:
            st.error(str(e))
elif "current" in st.session_state:
    r = st.session_state.current
    render_pipeline(pipeline, {k: "done" for k, *_ in AGENTS}, r.get("timings", {}))
else:
    render_pipeline(pipeline, {}, {})

if "current" in st.session_state:
    render_results(st.session_state.current)
