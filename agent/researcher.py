from concurrent.futures import ThreadPoolExecutor

from langchain_core.prompts import ChatPromptTemplate
from tools.search_tool import web_search


RESEARCHER_PROMPT = ChatPromptTemplate.from_template("""
You are an expert research agent. Using ONLY the numbered web sources below,
produce detailed research notes that follow the plan.

Rules:
- Organize notes under a heading for each key aspect in the plan.
- Cite sources inline with their number, e.g. [1] or [2][3], after every factual claim.
- Include concrete facts: numbers, dates, names, examples.
- Point out where sources disagree, and list any gaps the sources don't cover.
- Do not invent facts or sources.

Plan:
{plan}

Web sources:
{sources}
""")


def gather_sources(queries, max_results=3):
    """Run all search queries in parallel and dedupe results by URL."""
    with ThreadPoolExecutor(max_workers=len(queries) or 1) as pool:
        all_results = pool.map(lambda q: web_search(q, max_results=max_results), queries)

    sources, seen = [], set()
    for results in all_results:
        for r in results:
            if r["url"] and r["url"] not in seen:
                seen.add(r["url"])
                sources.append(r)
    return sources


def format_sources(sources):
    return "\n\n".join(
        f"[{i}] {s['title']}\nURL: {s['url']}\n{s['content']}"
        for i, s in enumerate(sources, 1)
    )


def researcher_agent(llm, plan, queries):
    """Returns (research_notes, sources)."""
    sources = gather_sources(queries)
    if not sources:
        sources_text = "No web results were found. Say so, and rely on general knowledge, flagging it as unverified."
    else:
        sources_text = format_sources(sources)

    chain = RESEARCHER_PROMPT | llm
    result = chain.invoke({"plan": plan, "sources": sources_text})

    reference_list = "\n".join(f"[{i}] {s['title']} - {s['url']}" for i, s in enumerate(sources, 1))
    research = result.content + (f"\n\nSources:\n{reference_list}" if sources else "")
    return research, sources
