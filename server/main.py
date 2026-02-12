from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from server.api.workflow import router as workflow_router
from server.api.projects import router as projects_router
from server.api.modules import router as modules_router
from server.api.artifacts import router as artifacts_router

from server.core.log_manager import log_manager
from utils.output_formatter import stdout_stream
from tools.manager import ToolManager
from utils.paths import get_project_root

# Log Listener Bridge
def log_bridge(text: str):
    try:
        # Get running loop (or try to)
        loop = asyncio.get_running_loop()
        if loop.is_running():
            asyncio.create_task(log_manager.emit_log("system", text))
    except RuntimeError:
        pass

# Initialize API
app = FastAPI(title="ReconFlow API")

# Initialize ToolManager
# We load modules once at startup
tool_manager = ToolManager()
tool_manager.load_yaml_modules(root_dirs=[str(get_project_root() / "modules")])
app.state.tool_manager = tool_manager

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(workflow_router, prefix="/api", tags=["Workflow"])
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(modules_router, prefix="/api/modules", tags=["Modules"])
app.include_router(artifacts_router, prefix="/api/projects", tags=["Artifacts"])

@app.get("/")
async def root():
    return {"message": "ReconFlow API is running", "status": "online"}

if __name__ == "__main__":
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
