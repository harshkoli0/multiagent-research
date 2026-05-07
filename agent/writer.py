from langchain_core.prompts import ChatPromptTemplate

def writer_agent(llm,content):
    prompt=ChatPromptTemplate.from_template("""
                                             you are a writer agent write a detailed article on the given content 
                                              content :{content}""")
    chain=prompt|llm
    result=chain.invoke({"content": content})
    return result.content