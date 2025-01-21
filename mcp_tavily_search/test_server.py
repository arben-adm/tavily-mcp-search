import pytest
from unittest.mock import AsyncMock, patch
from mcp.types import TextContent
from mcp_tavily_search.server import app

@pytest.fixture
def mock_tavily_client():
    with patch('mcp_tavily_search.server.AsyncTavilyClient') as mock:
        yield mock

@pytest.mark.asyncio
async def test_list_resources():
    resources = await app.list_resources()
    assert len(resources) == 1
    assert resources[0].name == "Web Search Example"
    assert resources[0].mimeType == "application/json"

@pytest.mark.asyncio
async def test_list_tools():
    tools = await app.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "search"
    assert "query" in tools[0].inputSchema["properties"]

@pytest.mark.asyncio
async def test_call_tool_search(mock_tavily_client):
    mock_tavily_client.return_value.search = AsyncMock(return_value={
        'answer': 'Test answer',
        'results': [
            {'title': 'Test Title', 'url': 'https://test.com', 'content': 'Test content'}
        ]
    })

    result = await app.call_tool("search", {"query": "test query"})
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "Test answer" in result[0].text
    assert "Test Title" in result[0].text
    assert "https://test.com" in result[0].text

@pytest.mark.asyncio
async def test_call_tool_invalid():
    result = await app.call_tool("invalid_tool", {})
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "Unknown tool" in result[0].text

@pytest.mark.asyncio
async def test_call_tool_search_invalid_args():
    result = await app.call_tool("search", {})
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "Invalid arguments" in result[0].text

@pytest.mark.asyncio
async def test_call_tool_search_error(mock_tavily_client):
    mock_tavily_client.return_value.search = AsyncMock(side_effect=Exception("API Error"))

    result = await app.call_tool("search", {"query": "test query"})
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "Search failed" in result[0].text
