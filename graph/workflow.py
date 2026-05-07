from typing import TypedDict

from langgraph.graph import StateGraph,END
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from agent.planner import planner_agent
from agent.researcher import researcher_agent
from agent.writer import writer_agent
from agent.Reviewer import reviewer_agent

load_dotenv()

llm=ChatGroq(model="llama-3.1-8b-instant",temperature=0)

class AgentState(TypedDict):
    query:str
    plan:str
    research:str
    draft:str
    final:str
    
def planner_node(state):
    plan=planner_agent(llm,state["query"])
    return {**state,"plan":plan}
    
def researcher_node(state):
    research=researcher_agent(llm,state["plan"])
    return {**state,"research":research}
    
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


# Compile App
app = workflow.compile()
    
    
    
    