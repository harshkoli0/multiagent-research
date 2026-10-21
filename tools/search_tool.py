from tavily import TavilyClient
from dotenv import load_dotenv
import os
load_dotenv()

_client = None


def get_client():
    """Create the Tavily client on first use, so importing this module doesn't require the API key."""
    global _client
    if _client is None:
        _client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return _client


def web_search(query, max_results=3, max_chars=1500):
    """Search the web and return a list of {title, url, content} dicts.
    Returns an empty list instead of raising if the search fails."""
    query = query[:350]
    try:
        response = get_client().search(query=query, max_results=max_results, search_depth="advanced")
    except Exception as e:
        print(f"[search] failed for '{query}': {e}")
        return []

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": (r.get("content") or "")[:max_chars],
        }
        for r in response.get("results", [])
    ]
