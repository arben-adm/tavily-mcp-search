from tavily import AsyncTavilyClient
from typing import Dict, Optional
import logging
import asyncio
from aiohttp import ClientError

logger = logging.getLogger(__name__)

class TavilySearchError(Exception):
    """Base exception for TavilySearchClient errors."""
    pass

class TavilySearchClient:
    def __init__(self, api_key: str):
        self.client = AsyncTavilyClient(api_key)
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    async def search(self, 
                    query: str,
                    search_depth: str = "advanced",
                    topic: str = "general",
                    max_results: int = 5,
                    include_images: bool = False,
                    include_raw_content: bool = False,
                    max_retries: int = 3) -> Dict:
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting search (attempt {attempt + 1}/{max_retries})")
                result = await self.client.search(
                    query=query,
                    search_depth=search_depth,
                    topic=topic,
                    max_results=max_results,
                    include_images=include_images,
                    include_answer=True,
                    include_raw_content=include_raw_content
                )
                logger.info("Search successful")
                return result
            except ClientError as e:
                logger.error(f"Network error on search attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise TavilySearchError(f"Max retries reached. Last error: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error on search attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise TavilySearchError(f"Max retries reached. Last error: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def get_search_context(self,
                                 query: str,
                                 max_tokens: int = 4000,
                                 **kwargs) -> str:
        try:
            results = await self.search(query, **kwargs)
            context = ""
            token_count = 0

            if 'answer' in results and results['answer']:
                context += f"AI Answer: {results['answer']}\n\n"
                token_count += len(results['answer'].split())

            for result in results.get('results', []):
                content = result.get('content', '')
                url = result.get('url', '')
                new_content = f"Source: {url}\n{content}\n\n"
                new_token_count = token_count + len(new_content.split())
                
                if new_token_count <= max_tokens:
                    context += new_content
                    token_count = new_token_count
                else:
                    break

            logger.info(f"Generated search context with {token_count} tokens")
            return context.strip()
        except TavilySearchError as e:
            logger.error(f"Failed to get search context: {str(e)}")
            raise

    async def qna_search(self,
                         query: str,
                         **kwargs) -> str:
        try:
            kwargs['search_depth'] = kwargs.get('search_depth', 'advanced')
            results = await self.search(query, **kwargs)
            answer = results.get('answer', 'No answer found.')
            logger.info(f"QnA search completed for query: {query}")
            return answer
        except TavilySearchError as e:
            logger.error(f"Failed to perform QnA search: {str(e)}")
            raise
