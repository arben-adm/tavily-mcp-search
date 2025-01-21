import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from mcp_tavily_search.client import TavilySearchClient

@pytest.fixture
def mock_tavily_client():
    with patch('mcp_tavily_search.client.AsyncTavilyClient') as mock:
        yield mock

@pytest.fixture
def tavily_search_client(mock_tavily_client):
    return TavilySearchClient('fake_api_key')

@pytest.mark.asyncio
async def test_search(tavily_search_client, mock_tavily_client):
    mock_tavily_client.return_value.search = AsyncMock(return_value={
        'answer': 'Test answer',
        'results': [
            {'title': 'Test Title', 'url': 'https://test.com', 'content': 'Test content'}
        ]
    })

    result = await tavily_search_client.search('test query')

    assert result['answer'] == 'Test answer'
    assert len(result['results']) == 1
    assert result['results'][0]['title'] == 'Test Title'

@pytest.mark.asyncio
async def test_get_search_context(tavily_search_client, mock_tavily_client):
    mock_tavily_client.return_value.search = AsyncMock(return_value={
        'answer': 'Test answer',
        'results': [
            {'title': 'Test Title', 'url': 'https://test.com', 'content': 'Test content'}
        ]
    })

    result = await tavily_search_client.get_search_context('test query', max_tokens=100)

    assert 'AI Answer: Test answer' in result
    assert 'Source: https://test.com' in result
    assert 'Test content' in result

@pytest.mark.asyncio
async def test_qna_search(tavily_search_client, mock_tavily_client):
    mock_tavily_client.return_value.search = AsyncMock(return_value={
        'answer': 'Test answer',
    })

    result = await tavily_search_client.qna_search('test query')

    assert result == 'Test answer'

@pytest.mark.asyncio
async def test_search_retry(tavily_search_client, mock_tavily_client):
    mock_search = AsyncMock(side_effect=[Exception("API Error"), {'answer': 'Test answer'}])
    mock_tavily_client.return_value.search = mock_search

    result = await tavily_search_client.search('test query')

    assert result['answer'] == 'Test answer'
    assert mock_search.call_count == 2

@pytest.mark.asyncio
async def test_search_max_retries_exceeded(tavily_search_client, mock_tavily_client):
    mock_search = AsyncMock(side_effect=Exception("API Error"))
    mock_tavily_client.return_value.search = mock_search

    with pytest.raises(Exception, match="API Error"):
        await tavily_search_client.search('test query', max_retries=3)

    assert mock_search.call_count == 3
