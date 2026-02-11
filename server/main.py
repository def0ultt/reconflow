from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from server.api import workflow
from server.core.log_manager import log_manager
from utils.output_formatter import stdout_stream

# Log Listener Bridge
def log_bridge(text: str):
    try:
        # Get running loop (or try to)
        loop = asyncio.get_running_loop()
        if loop.is_running():
            asyncio.create_task(log_manager.emit_log("system", text))
    except RuntimeError:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    stdout_stream.add_listener(log_bridge)
    yield
    # Shutdown
    stdout_stream.remove_listener(log_bridge)

# Initialize API
app = FastAPI(
    title="ReconFlow API",
    description="Backend API for ReconFlow SaaS (Localhost MVP)",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(workflow.router, prefix="/api", tags=["Workflow"])

@app.get("/")
async def root():
    return {"message": "ReconFlow API is running", "status": "online"}

if __name__ == "__main__":
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
