import os
import json
import logging
import sys
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

# Force UTF-8 encoding for stdout
if sys.platform.startswith('win'):
    import locale
    sys.stdout.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

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
                        "enum": ["basic", "advanced"],
                        "default": "advanced"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Search topic (general or news)",
                        "enum": ["general", "news"],
                        "default": "general"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    },
                    "include_images": {
                        "type": "boolean",
                        "description": "Include images in the results",
                        "default": False
                    },
                    "include_raw_content": {
                        "type": "boolean",
                        "description": "Include raw content in the results",
                        "default": False
                    }
                },
                "required": ["query"]
            }
        )
    ]
    return tools

async def process_search_results(results: dict) -> TextContent:
    """Process search results into TextContent"""
    try:
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
                title = result.get('title', 'No title')
                url = result.get('url', 'No URL')
                content = result.get('content', 'No content')
                
                response_text.append(f"\n{i}. {title}")
                response_text.append(f"URL: {url}")
                response_text.append(f"Summary: {content}\n")

        if 'images' in results and results['images']:
            response_text.append("\nRelated Images:")
            for image in results['images']:
                if isinstance(image, dict):
                    response_text.append(f"URL: {image['url']}")
                    response_text.append(f"Description: {image['description']}\n")
                else:
                    response_text.append(f"URL: {image}\n")

        return TextContent(
            type="text",
            text="\n".join(response_text) if response_text else "No relevant information found."
        )
    except Exception as e:
        logger.error(f"Error processing search results: {str(e)}")
        return TextContent(
            type="text",
            text="Error processing search results. Please try again."
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
        search_depth = arguments.get("search_depth", "advanced")
        topic = arguments.get("topic", "general")
        max_results = arguments.get("max_results", 5)
        include_images = arguments.get("include_images", False)
        include_raw_content = arguments.get("include_raw_content", False)
        
        results = await client.search(
            query=query,
            search_depth=search_depth,
            topic=topic,
            max_results=max_results,
            include_images=include_images,
            include_answer=True,
            include_raw_content=include_raw_content
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
    finally:
        logger.info("Server shutting down")

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
