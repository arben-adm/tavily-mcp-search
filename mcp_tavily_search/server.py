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
MAX_RETRIES = 3
TIMEOUT = 120.0  # seconds

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

def sanitize_query(query: str) -> str:
    """Sanitize the search query."""
    if not query or not isinstance(query, str):
        raise ValueError("Invalid query provided")
    return query.strip()

async def execute_tavily_search(query: str, config: SearchConfig, retry_count: int = 0) -> Dict[str, Any]:
    """Execute a search using the Tavily API with retry logic"""
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not found in environment variables")

    sanitized_query = sanitize_query(query)
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": sanitized_query,
            "search_depth": config.search_depth,
            "topic": config.topic,
            "days": config.days,
            "max_results": config.max_results,
            "include_answer": config.include_answer
        }

        try:
            response = await client.post(TAVILY_BASE_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Validate response structure
            if "results" not in data:
                raise ValueError("Invalid API response structure")
                
            return data

        except httpx.TimeoutException:
            if retry_count < MAX_RETRIES:
                await asyncio.sleep(1 * (retry_count + 1))  # Exponential backoff
                return await execute_tavily_search(query, config, retry_count + 1)
            raise ValueError(f"Timeout after {MAX_RETRIES} retries")

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error occurred: {e.response.status_code}"
            if e.response.status_code == 401:
                error_msg = "Invalid API key"
            elif e.response.status_code == 429:
                error_msg = "Rate limit exceeded"
            raise ValueError(error_msg)

        except Exception as e:
            raise ValueError(f"Error executing search: {str(e)}")

async def combine_search_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine and deduplicate search results from multiple searches"""
    seen_urls = set()
    combined_results = []
    
    for result in results:
        if not isinstance(result, dict) or "results" not in result:
            continue
            
        for item in result.get("results", []):
            if not isinstance(item, dict) or "url" not in item:
                continue
                
            if item["url"] not in seen_urls and len(seen_urls) < MIN_SEARCH_RESULTS:
                seen_urls.add(item["url"])
                combined_results.append(item)
    
    # Ensure we have minimum required results
    if not combined_results:
        raise ValueError("No valid results found")
        
    return {
        "results": combined_results,
        "answer": "\n\n".join(r.get("answer", "") for r in results if isinstance(r, dict) and r.get("answer")),
    }

@mcp.tool()
async def comprehensive_search(query: str) -> str:
    """
    Perform a comprehensive search across multiple topics using Tavily.
    
    Args:
        query: The search query to research
    """
    try:
        # Validate and sanitize input
        sanitized_query = sanitize_query(query)
        
        # Execute searches for each topic in parallel
        search_tasks = [
            execute_tavily_search(f"{sanitized_query} {topic}", config)
            for topic, config in TOPIC_CONFIGS.items()
        ]
        
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Filter out failed searches
        valid_results = [
            result for result in search_results 
            if isinstance(result, dict) and not isinstance(result, Exception)
        ]
        
        if not valid_results:
            return "Error: No valid search results found. Please try again."
            
        combined_results = await combine_search_results(valid_results)
        
        # Format the response
        response_parts = ["## Research Results\n"]
        
        if combined_results.get("answer"):
            response_parts.append(f"### Summary\n{combined_results['answer']}\n")
        
        response_parts.append("### Detailed Sources")
        
        for idx, result in enumerate(combined_results["results"], 1):
            title = result.get("title", "No Title")
            url = result.get("url", "#")
            content = result.get("content", "No content available")
            
            response_parts.append(
                f"{idx}. [{title}]({url})\n"
                f"   - {content[:300]}...\n"
            )
        
        return "\n".join(response_parts)
        
    except ValueError as ve:
        return f"Error: {str(ve)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def main():
    """Entry point for the MCP server."""
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()