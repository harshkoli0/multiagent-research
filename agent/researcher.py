from langchain_core.prompts import ChatPromptTemplate
from tools.search_tool import web_search

def researcher_agent(llm,topic):
    web_result=web_search(topic)
    
    prompt=ChatPromptTemplate.from_template(
        """you are the best research agent.
        use the web search result below ]to research the topic deeply
        topic:{topic}
        web results:{web_result}"""
    )
    
    chain=prompt|llm
    result =chain.invoke({"topic": topic,"web_result": web_result})
    return result.content
