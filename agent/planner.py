from langchain_core.prompts import ChatPromptTemplate

def planner_agent(llm,query):
    prompt=ChatPromptTemplate.from_template("""
                                             you are a planner agent break the user query into clear actionable steps 
                                              Query :{query}""")
    chain=prompt|llm
    result=chain.invoke({"query": query})
    return result.content