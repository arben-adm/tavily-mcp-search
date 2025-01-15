from tavily import AsyncTavilyClient
from typing import Dict, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

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
                    search_depth: str = "basic",
                    max_retries: int = 3) -> Dict:
        for attempt in range(max_retries):
            try:
                return await self.client.search(
                    query=query,
                    search_depth=search_depth,
                    include_images=False,
                    include_answer=True,
                    max_results=5
                )
            except Exception as e:
                logger.error(f"Search attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))
