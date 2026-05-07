from tavily import TavilyClient
from dotenv import load_dotenv
import os 
load_dotenv()

client=TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))



def web_search(query):
    query = query[:350]
    response=client.search(query=query,max_results=3,search_depth="advanced")
    
    
    return response["results"]