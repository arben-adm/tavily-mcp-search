import os
import json
import logging
from datetime import datetime
from collections.abc import Sequence
from typing import Any, Optional
from tavily import AsyncTavilyClient
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    EmptyResult
)
from pydantic import AnyUrl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tavily-search-server")

# Load environment variables
load_dotenv()

# Get API key
API_KEY = os.getenv("TAVILY_API_KEY")
if not API_KEY:
    logger.error("TAVILY_API_KEY environment variable not found")
    raise ValueError("TAVILY_API_KEY environment variable required")

# Initialize server
app = Server("tavily-search-server")

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources"""
    logger.info("Listing available resources")
    resources = [
        Resource(
            uri=AnyUrl("websearch://query=example,search_depth=basic", scheme="websearch"),
            name="Web Search Example",
            mimeType="application/json",
            description="General web search using Tavily API"
        )
    ]
    return resources

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    logger.info("Listing available tools")
    tools = [
        Tool(
            name="search",
            description="Search the web using Tavily API",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "search_depth": {
                        "type": "string",
                        "description": "Search depth (basic or advanced)",
                        "enum": ["basic", "advanced"]
                    }
                },
                "required": ["query"]
            }
        )
    ]
    return tools

async def process_search_results(results: dict) -> TextContent:
    """Process search results into TextContent"""
    if not results:
        return TextContent(
            type="text",
            text="No results found for your query."
        )

    response_text = []
    
    if 'answer' in results and results['answer']:
        response_text.append("AI Answer:")
        response_text.append(results['answer'])
        response_text.append("\n")

    if 'results' in results and results['results']:
        response_text.append("Search Results:")
        for i, result in enumerate(results['results'], 1):
            response_text.append(f"\n{i}. {result.get('title', 'No title')}")
            response_text.append(f"URL: {result.get('url', 'No URL')}")
            response_text.append(f"Summary: {result.get('snippet', 'No summary')}\n")

    return TextContent(
        type="text",
        text="\n".join(response_text) if response_text else "No relevant information found."
    )

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    if name != "search":
        return [TextContent(
            type="text",
            text=f"Unknown tool '{name}'. Only 'search' is supported."
        )]

    if not isinstance(arguments, dict) or "query" not in arguments:
        return [TextContent(
            type="text",
            text="Invalid arguments. A 'query' parameter is required."
        )]

    try:
        client = AsyncTavilyClient(API_KEY)
        query = arguments["query"]
        search_depth = arguments.get("search_depth", "basic")
        
        results = await client.search(
            query=query,
            search_depth=search_depth,
            include_images=False,
            include_answer=True,
            max_results=3
        )
        
        return [await process_search_results(results)]

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Search failed: {str(e)}"
        )]

async def main():
    """Main entry point"""
    logger.info("Starting Tavily search server")
    try:
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server failed: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
