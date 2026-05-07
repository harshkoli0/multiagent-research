from langchain_core.prompts import ChatPromptTemplate

def reviewer_agent(llm,content):
    prompt=ChatPromptTemplate.from_template("""you are the Reviewer agent
                                             improve the grammer,clarity,formatting ,readabitliy content:{content}""")
    
    chain=prompt|llm
    result=chain.invoke({"content": content})
    return result.content