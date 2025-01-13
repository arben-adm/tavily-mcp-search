from typing import Optional, Dict, Any, Set
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

# more advanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()

class ConnectionState(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    RECOVERING = "recovering"

@dataclass
class TokenBucket:
    """Rate Limiter mit Token Bucket Algorithmus"""
    capacity: int = 20
    tokens: float = field(default=20.0)
    last_update: float = field(default_factory=time.time)
    rate: float = 20.0
    min_tokens: float = 1.0

    def has_capacity(self) -> bool:
        self._add_tokens()
        return self.tokens >= self.min_tokens

    async def acquire(self) -> bool:
        while not self.has_capacity():
            await asyncio.sleep(0.1)
        self.tokens -= self.min_tokens
        return True

    def _add_tokens(self):
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

@dataclass
class ConnectionManager:
    state: ConnectionState = ConnectionState.DISCONNECTED
    last_health_check: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    max_errors: int = 15  # higher error threshold
    health_check_interval: timedelta = field(default_factory=lambda: timedelta(seconds=60))
    recovery_attempts: int = 0
    max_recovery_attempts: int = 5
    
    def is_healthy(self) -> bool:
        return (
            self.state in [ConnectionState.CONNECTED, ConnectionState.CONNECTING, ConnectionState.RECOVERING]
            and self.error_count < self.max_errors
        )

    def record_error(self) -> None:
        self.error_count += 1
        if self.error_count >= self.max_errors:
            logger.warning(f"Error count high: {self.error_count}/{self.max_errors}")
            if self.can_attempt_recovery():
                self.state = ConnectionState.RECOVERING
            else:
                self.state = ConnectionState.ERROR

    def record_success(self) -> None:
        if self.error_count > 0:
            self.error_count = max(0, self.error_count - 1)
        self.last_health_check = datetime.now()
        self.state = ConnectionState.CONNECTED
        self.recovery_attempts = 0

    def can_attempt_recovery(self) -> bool:
        return self.recovery_attempts < self.max_recovery_attempts

    def attempt_recovery(self) -> bool:
        if self.can_attempt_recovery():
            self.recovery_attempts += 1
            self.error_count = max(0, self.error_count - 2)
            self.state = ConnectionState.RECOVERING
            return True
        return False

@dataclass
class RequestQueue:
    max_concurrent: int = 20
    active_requests: Set[asyncio.Task] = field(default_factory=set)
    token_bucket: TokenBucket = field(default_factory=TokenBucket)
    
    async def add_request(self, coro):
        await self.token_bucket.acquire()
        
        task = asyncio.create_task(coro)
        self.active_requests.add(task)
        
        def cleanup(future):
            self.active_requests.discard(future)
            if future.exception():
                logger.error(f"Task failed: {future.exception()}")
            
        task.add_done_callback(cleanup)
        return task

class RobustMCPServer:
    def __init__(self, name: str, api_key: str):
        self.mcp = FastMCP(name)
        self.api_key = api_key
        self.conn_manager = ConnectionManager()
        self.request_queue = RequestQueue()
        self.shutdown_event = asyncio.Event()
        
        # Erweiterte Timeouts
        self.timeout = httpx.Timeout(60.0, connect=20.0, read=40.0, write=20.0)
        self.max_retries = 5
        self.base_backoff = 0.5
        
        self.health_check_thread = None
        self._register_handlers()

    def _register_handlers(self):
        @self.mcp.tool()
        async def comprehensive_search(query: str) -> str:
            """Durchführung einer umfassenden Websuche"""
            return await self._handle_search(query)

    async def _handle_search(self, query: str) -> str:
        try:
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as client:
                search_coro = self._execute_with_retry(self._perform_search, client, query)
                task = await self.request_queue.add_request(search_coro)
                try:
                    # Erhöhter Timeout für die gesamte Operation
                    response = await asyncio.wait_for(task, timeout=65.0)
                    self.conn_manager.record_success()
                    return self._format_response(response)
                except asyncio.TimeoutError:
                    self.conn_manager.record_error()
                    logger.error("Search request timed out")
                    return "Die Suchanfrage hat zu lange gedauert. Bitte versuchen Sie es erneut."
                except Exception as e:
                    self.conn_manager.record_error()
                    logger.error(f"Search task error: {str(e)}")
                    return "Bei der Verarbeitung der Suche ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut."
        except Exception as e:
            error_msg = f"Search error: {str(e)}"
            logger.error(error_msg)
            return f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"

    async def _perform_search(self, client: httpx.AsyncClient, query: str) -> Dict[str, Any]:
        payload = {
            "api_key": self.api_key,
            "query": query,
            "include_domains": [],
            "exclude_domains": [],
            "max_results": 10  # Limit 
        }
        
        headers = {
            "User-Agent": "TavilyMCPServer/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        try:
            response = await client.post(
                "https://api.tavily.com/search",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during search: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search: {str(e)}")
            raise

    async def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    logger.error(f"Final retry attempt failed: {str(e)}")
                    raise
                wait_time = self.base_backoff * (1.5 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time:.1f}s: {str(e)}")
                await asyncio.sleep(wait_time)
        
        raise last_exception

    def _format_response(self, data: Dict[str, Any]) -> str:
        try:
            results = data.get("results", [])
            if not results:
                return "Keine Ergebnisse gefunden. Bitte versuchen Sie eine andere Suchanfrage."
                
            formatted = ["## Suchergebnisse\n"]
            for idx, result in enumerate(results[:10], 1):
                title = result.get('title', 'Kein Titel').strip()
                url = result.get('url', '#').strip()
                content = result.get('content', 'Kein Inhalt verfügbar').strip()
                
                formatted.extend([
                    f"{idx}. {title}",
                    f"   URL: {url}",
                    f"   {content[:250]}...\n"  
                ])
                
            return "\n".join(formatted)
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            return "Fehler beim Formatieren der Suchergebnisse."

    async def _health_check(self):
        """Verbesserte Health Check Logik mit Recovery-Mechanismus"""
        while not self.shutdown_event.is_set():
            try:
                if not self.conn_manager.is_healthy():
                    if self.conn_manager.state == ConnectionState.ERROR:
                        if self.conn_manager.attempt_recovery():
                            logger.info("Starting recovery attempt...")
                            await asyncio.sleep(5)  # Kurze Pause vor Recovery
                        else:
                            logger.error("Maximum recovery attempts reached")
                            await self.shutdown()
                            break
                    else:
                        logger.warning("Health check failed, system unhealthy")
                
                if self.conn_manager.state == ConnectionState.RECOVERING:
                    logger.info("System in recovery mode")
                
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                if not self.conn_manager.attempt_recovery():
                    logger.error("Health check system failed, initiating shutdown")
                    await self.shutdown()
                    break
                await asyncio.sleep(5)

    def start(self):
        """Server-Start mit verbessertem Error Handling"""
        try:
            logger.info("Starting MCP server...")
            self.conn_manager.state = ConnectionState.CONNECTING
            
            # Health Check Thread start
            self.health_check_thread = threading.Thread(
                target=self._run_health_check,
                daemon=True
            )
            self.health_check_thread.start()
            
            # MCP Server start
            self.mcp.run(transport='stdio')
            
        except Exception as e:
            logger.error(f"Server startup error: {str(e)}")
            self.conn_manager.state = ConnectionState.ERROR
            raise

    def _run_health_check(self):
        """Health Check Thread mit Error Handling"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._health_check())
        except Exception as e:
            logger.error(f"Health check thread error: {str(e)}")
        finally:
            loop.close()

    async def shutdown(self):
        """Graceful Shutdown mit Cleanup"""
        logger.info("Initiating server shutdown...")
        self.shutdown_event.set()
        self.conn_manager.state = ConnectionState.DISCONNECTED
        
        # Aktive Requests beenden
        for task in self.request_queue.active_requests:
            task.cancel()
        
        if self.request_queue.active_requests:
            await asyncio.wait(self.request_queue.active_requests)
        
        logger.info("Server shutdown complete")

if __name__ == "__main__":
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY environment variable is required")
        sys.exit(1)

    server = RobustMCPServer("tavily-search", api_key)
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        asyncio.run(server.shutdown())
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        try:
            asyncio.run(server.shutdown())
        except:
            pass
        sys.exit(1)