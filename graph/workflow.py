from typing import TypedDict

from langgraph.graph import StateGraph,END
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

from agent.planner import planner_agent
from agent.researcher import researcher_agent
from agent.writer import writer_agent
from agent.Reviewer import reviewer_agent

load_dotenv()

DEFAULT_MODEL=os.getenv("GROQ_MODEL","openai/gpt-oss-20b")

class AgentState(TypedDict):
    query:str
    plan:str
    search_queries:list[str]
    sources:list[dict]
    research:str
    draft:str
    final:str
    
def build_app(model=DEFAULT_MODEL):
    """Build and compile the planner -> research -> writer -> reviewer graph for the given Groq model."""
    llm=ChatGroq(model=model,temperature=0)

    def planner_node(state):
        plan,queries=planner_agent(llm,state["query"])
        return {**state,"plan":plan,"search_queries":queries}

    def researcher_node(state):
        research,sources=researcher_agent(llm,state["plan"],state["search_queries"])
        return {**state,"research":research,"sources":sources}

    def writer_node(state):
        draft=writer_agent(llm,state["research"])

        return {**state,"draft":draft}
    def reviewer_node(state):
        final=reviewer_agent(llm,state["draft"])
        return {**state,"final":final}

    workflow=StateGraph(AgentState)

    workflow.add_node(
        "planner",
        planner_node
    )

    workflow.add_node(
        "research",
        researcher_node
    )

    workflow.add_node(
        "writer",
        writer_node
    )

    workflow.add_node(
        "reviewer",
        reviewer_node
    )


    # Entry Point
    workflow.set_entry_point("planner")


    # Add Edges
    workflow.add_edge(
        "planner",
        "research"
    )

    workflow.add_edge(
        "research",
        "writer"
    )

    workflow.add_edge(
        "writer",
        "reviewer"
    )

    workflow.add_edge(
        "reviewer",
        END
    )

    return workflow.compile()
