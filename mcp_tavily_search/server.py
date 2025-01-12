from typing import Optional, Dict, Any
import asyncio
import httpx
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

# Logging and Environment Variables Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

class ConnectionState(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class ConnectionManager:
    state: ConnectionState = ConnectionState.DISCONNECTED
    last_health_check: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    max_errors: int = 3
    health_check_interval: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    
    def is_healthy(self) -> bool:
        return (
            self.state == ConnectionState.CONNECTED 
            and self.error_count < self.max_errors
            and datetime.now() - self.last_health_check < self.health_check_interval
        )

    def record_error(self) -> None:
        self.error_count += 1
        if self.error_count >= self.max_errors:
            self.state = ConnectionState.ERROR
            logger.error("Too many errors occurred, marking connection as unhealthy")

    def record_success(self) -> None:
        self.error_count = 0
        self.last_health_check = datetime.now()
        self.state = ConnectionState.CONNECTED

@dataclass
class RequestQueue:
    """Manages concurrent requests with rate-limiting"""
    max_concurrent: int = 5
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    active_requests: int = 0
    semaphore: asyncio.Semaphore = field(default_factory=lambda: asyncio.Semaphore(5))
    
    async def add_request(self, coro):
        await self.queue.put(coro)
        asyncio.create_task(self._process_queue())
    
    async def _process_queue(self):
        if self.active_requests >= self.max_concurrent:
            return
            
        async with self.semaphore:
            self.active_requests += 1
            try:
                coro = await self.queue.get()
                await coro
            finally:
                self.active_requests -= 1
                self.queue.task_done()

class RobustMCPServer:
    def __init__(self, name: str, api_key: str):
        self.mcp = FastMCP(name)
        self.api_key = api_key
        self.conn_manager = ConnectionManager()
        self.request_queue = RequestQueue()
        self.shutdown_event = asyncio.Event()
        
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.max_retries = 3
        self.base_backoff = 1.0
        
        self.health_check_thread = None
        
        self._register_handlers()
        
    def _register_handlers(self):
        @self.mcp.tool()
        async def comprehensive_search(query: str) -> str:
            return await self._handle_search(query)

    def start(self):  # Changed to sync method
        """Start the server with Health Monitoring"""
        try:
            logger.info("Starting MCP server...")
            self.conn_manager.state = ConnectionState.CONNECTING
            
            # Start health check in separate thread
            self.health_check_thread = threading.Thread(
                target=self._run_health_check,
                daemon=True
            )
            self.health_check_thread.start()
            
            # Run MCP server synchronously
            self.mcp.run(transport='stdio')
            
        except Exception as e:
            logger.error(f"Server startup error: {str(e)}")
            self.conn_manager.state = ConnectionState.ERROR
            raise

    def _run_health_check(self):
        """Run health check in separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._health_check())
        finally:
            loop.close()

    async def shutdown(self):
        """Cleanup resources"""
        self.shutdown_event.set()
        self.conn_manager.state = ConnectionState.DISCONNECTED
        
    async def _health_check(self):
        while not self.shutdown_event.is_set():
            try:
                if not self.conn_manager.is_healthy():
                    logger.warning("Health check failed, attempting recovery...")
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                await asyncio.sleep(5)

    async def _handle_search(self, query: str) -> str:
        """Behandle Suchanfragen mit Fehlerbehandlung."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Wrap the search in a coroutine
                search_coro = self._execute_with_retry(
                    self._perform_search,
                    client,
                    query
                )
                # Add to request queue
                await self.request_queue.add_request(search_coro)
                response = await search_coro
                self.conn_manager.record_success()
                return self._format_response(response)
        except Exception as e:
            error_msg = f"Search error: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def _perform_search(self, client: httpx.AsyncClient, query: str) -> Dict[str, Any]:
        """Führe die eigentliche Suchanfrage durch."""
        payload = {
            "api_key": self.api_key,
            "query": query
        }
        
        response = await client.post(
            "https://api.tavily.com/search",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    async def _execute_with_retry(self, func, *args, **kwargs):
        """Execute with retry logic"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = self.base_backoff * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                await asyncio.sleep(wait_time)

    def _format_response(self, data: Dict[str, Any]) -> str:
        """Formatiere die Suchergebnisse."""
        try:
            results = data.get("results", [])
            if not results:
                return "No results found."
                
            formatted = ["## Search Results\n"]
            for idx, result in enumerate(results, 1):
                formatted.extend([
                    f"{idx}. {result.get('title', 'No Title')}",
                    f"   URL: {result.get('url', '#')}",
                    f"   {result.get('content', 'No content available')[:300]}...\n"
                ])
                
            return "\n".join(formatted)
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            return "Error formatting search results."

if __name__ == "__main__":
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable is required")

    server = RobustMCPServer("tavily-search", api_key)
    try:
        server.start()  # Now synchronous call
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)