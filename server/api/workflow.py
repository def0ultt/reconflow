from fastapi import APIRouter, WebSocket, BackgroundTasks, HTTPException
from fastapi.websockets import WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import asyncio
import json

from core.schema import ModuleSchema
from core.yaml_module import GenericYamlModule
from core.context import Context
from server.core.log_manager import log_manager

router = APIRouter()

class RunRequest(BaseModel):
    workflow: ModuleSchema
    variables: Dict[str, Any] = {}

@router.post("/run")
async def run_workflow(request: RunRequest, background_tasks: BackgroundTasks):
    """
    Execute a workflow definition provided in the request body.
    """
    execution_id = str(uuid.uuid4())
    
    # Run in background
    background_tasks.add_task(_execute_workflow, execution_id, request.workflow, request.variables)
    
    return {"execution_id": execution_id, "status": "started"}

async def _execute_workflow(execution_id: str, schema: ModuleSchema, variables: Dict[str, Any]):
    """Background execution wrapper"""
    try:
        await log_manager.emit_log(execution_id, f"[INFO] Starting execution {execution_id}\n")
        
        # Initialize Module
        module = GenericYamlModule()
        module.load_from_schema(schema)
        
        # Initialize Context
        ctx = Context()
        
        # Inject variables into context (if needed/supported)
        # We might need to manually update module options or context settings
        # For now, let's just pass them as options if they match
        for key, value in variables.items():
            if key in module.options:
                module.update_option(key, value)
        
        # Run (Blocking call, hence running in thread pool via FastAPI background task or we should use loop.run_in_executor)
        # FastAPI BackgroundTasks run in a thread pool, so blocking is okay-ish for MVP.
        # But extensive blocking might starve the pool. Ideally use asyncio or dedicated thread.
        # Since GenericYamlModule uses its own ThreadPoolExecutor, checking it doesn't block main loop is important.
        
        # GenericYamlModule.run is synchronous.
        # We should run it in a separate thread to avoid blocking the async event loop if it wasn't already.
        # FastAPI's background_tasks run sync functions in a threadpool. `_execute_workflow` is async, so it runs on loop.
        # We must wrap the blocking call.
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: module.run(ctx, background=False))
        
        await log_manager.emit_log(execution_id, f"\n[INFO] Execution {execution_id} completed.\n")
        
    except Exception as e:
        await log_manager.emit_log(execution_id, f"\n[ERROR] Execution failed: {str(e)}\n")

@router.websocket("/ws/logs/{execution_id}")
async def websocket_endpoint(websocket: WebSocket, execution_id: str):
    await websocket.accept()
    queue = await log_manager.subscribe(execution_id)
    
    try:
        while True:
            # Check if client is still alive
            data = await queue.get()
            # Send log line
            await websocket.send_text(data)
    except WebSocketDisconnect:
        log_manager.unsubscribe(execution_id, queue)
