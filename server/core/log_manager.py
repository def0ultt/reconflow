import asyncio
from typing import List, Dict, Callable
from collections import defaultdict

class LogManager:
    """
    Simple in-memory log manager for the MVP.
    Stores logs and manages WebSocket subscribers.
    """
    def __init__(self):
        self._logs: Dict[str, List[str]] = defaultdict(list)
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)

    async def emit_log(self, execution_id: str, message: str):
        """Save log and push to subscribers"""
        self._logs[execution_id].append(message)
        
        # Notify subscribers
        if execution_id in self._subscribers:
            for queue in self._subscribers[execution_id]:
                await queue.put(message)

    async def subscribe(self, execution_id: str) -> asyncio.Queue:
        """Subscribe to logs for an execution ID"""
        queue = asyncio.Queue()
        self._subscribers[execution_id].append(queue)
        
        # Replay existing logs
        for log in self._logs[execution_id]:
            await queue.put(log)
            
        return queue

    def unsubscribe(self, execution_id: str, queue: asyncio.Queue):
        if execution_id in self._subscribers:
            if queue in self._subscribers[execution_id]:
                self._subscribers[execution_id].remove(queue)

log_manager = LogManager()
