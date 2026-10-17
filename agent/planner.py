import re
from typing import List

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate


class ResearchPlan(BaseModel):
    objective: str = Field(description="One sentence describing what the final article must achieve")
    audience: str = Field(description="Who the article is for, e.g. beginners, executives, developers")
    key_aspects: List[str] = Field(description="3-6 subtopics the article must cover")
    search_queries: List[str] = Field(description="3-5 short, specific web search queries, one per key aspect")
    steps: List[str] = Field(description="Ordered, actionable steps to research and write the article")


PLANNER_PROMPT = ChatPromptTemplate.from_template("""
You are a planner agent in a multi-agent research team (planner -> researcher -> writer -> reviewer).
Break the user query into a clear, actionable research plan.

Guidelines:
- Identify the real intent behind the query and the likely audience.
- Split the topic into 3-6 distinct key aspects with no overlap.
- Write 3-5 web search queries (under 15 words each) that together cover every key aspect.
  Prefer specific queries (include years, names, metrics) over vague ones.
- Steps must be concrete and ordered.

Query: {query}
""")


def _strip_number(step: str) -> str:
    # The model sometimes numbers steps itself ("1. ..."); avoid "1. 1. ..."
    return re.sub(r'^\s*\d+[.)]\s*', '', step)


def format_plan(plan: ResearchPlan) -> str:
    lines = [
        f"Objective: {plan.objective}",
        f"Audience: {plan.audience}",
        "Key aspects:",
        *[f"  - {a}" for a in plan.key_aspects],
        "Search queries:",
        *[f"  - {q}" for q in plan.search_queries],
        "Steps:",
        *[f"  {i}. {_strip_number(s)}" for i, s in enumerate(plan.steps, 1)],
    ]
    return "\n".join(lines)


def planner_agent(llm, query, max_queries=5):
    """Returns (plan_text, search_queries)."""
    try:
        chain = PLANNER_PROMPT | llm.with_structured_output(ResearchPlan)
        plan = chain.invoke({"query": query})
        queries = [q.strip() for q in plan.search_queries if q.strip()][:max_queries]
        return format_plan(plan), queries or [query]
    except Exception as e:
        # Fall back to a free-text plan if the model can't produce structured output
        print(f"[planner] structured output failed ({e}); falling back to text plan")
        result = (PLANNER_PROMPT | llm).invoke({"query": query})
        return result.content, [query]
