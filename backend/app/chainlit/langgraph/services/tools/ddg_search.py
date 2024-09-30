from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


@tool
async def ddg_search(query: str) -> str:
    """Searches DuckDuckGo for a query and returns the results."""
    wrapper = DuckDuckGoSearchAPIWrapper(region="jp-jp", max_results=5)
    search = DuckDuckGoSearchResults(api_wrapper=wrapper, source="text")
    return search.invoke(query)