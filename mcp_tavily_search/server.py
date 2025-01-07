from typing import List, Dict, Any, Optional
import os
import httpx
import asyncio
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("tavily-search")

# Constants
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_BASE_URL = "https://api.tavily.com/search"
MIN_SEARCH_RESULTS = 8

@dataclass
class SearchConfig:
    """Search configuration for different topic areas"""
    search_depth: str
    topic: str
    days: int = 3
    max_results: int = 10
    include_answer: bool = True

# Define search configurations for different topics
TOPIC_CONFIGS = {
    "business": SearchConfig("advanced", "general", max_results=12),
    "news": SearchConfig("basic", "news", days=1, max_results=10),
    "finance": SearchConfig("advanced", "general", max_results=12),
    "politics": SearchConfig("basic", "news", days=2, max_results=10),
}

async def execute_tavily_search(query: str, config: SearchConfig) -> Dict[str, Any]:
    """Execute a search using the Tavily API"""
    async with httpx.AsyncClient() as client:
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": config.search_depth,
            "topic": config.topic,
            "days": config.days,
            "max_results": config.max_results,
            "include_answer": config.include_answer
        }
        
        response = await client.post(TAVILY_BASE_URL, json=payload)
        response.raise_for_status()
        return response.json()

async def combine_search_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine and deduplicate search results from multiple searches"""
    seen_urls = set()
    combined_results = []
    
    for result in results:
        for item in result.get("results", []):
            if item["url"] not in seen_urls and len(seen_urls) < MIN_SEARCH_RESULTS:
                seen_urls.add(item["url"])
                combined_results.append(item)
    
    # Ensure we have minimum required results
    if len(combined_results) < MIN_SEARCH_RESULTS:
        raise ValueError(f"Could not find minimum {MIN_SEARCH_RESULTS} unique results")
        
    return {
        "results": combined_results,
        "answer": "\n\n".join(r.get("answer", "") for r in results if r.get("answer")),
    }

@mcp.tool()
async def comprehensive_search(query: str) -> str:
    """
    Perform a comprehensive search across multiple topics using Tavily.
    
    Args:
        query: The search query to research
    """
    # Execute searches for each topic in parallel
    search_tasks = [
        execute_tavily_search(f"{query} {topic}", config)
        for topic, config in TOPIC_CONFIGS.items()
    ]
    
    try:
        search_results = await asyncio.gather(*search_tasks)
        combined_results = await combine_search_results(search_results)
        
        # Format the response
        response_parts = ["## Research Results\n"]
        
        if combined_results.get("answer"):
            response_parts.append(f"### Summary\n{combined_results['answer']}\n")
        
        response_parts.append("### Detailed Sources")
        for idx, result in enumerate(combined_results["results"], 1):
            response_parts.append(
                f"{idx}. [{result['title']}]({result['url']})\n"
                f"   - {result['content'][:300]}...\n"
            )
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"Error performing research: {str(e)}"

def main():
    """Entry point for the MCP server."""
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()