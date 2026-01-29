from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator

# --- Shared Components ---

class InfoBlock(BaseModel):
    id: str
    name: str = "Unknown"
    author: str = "Unknown"
    description: str = ""

class VarConfig(BaseModel):
    default: Optional[Any] = None
    required: bool = False

class OutputConfig(BaseModel):
    path: Optional[str] = None
    filename: Optional[str] = None

# --- Module Specific ---

class ModuleStep(BaseModel):
    name: str
    tool: str
    args: str = ""
    capture: bool = False
    stdin: bool = False
    timeout: Optional[str] = None
    condition: Optional[str] = None
    output: Optional[OutputConfig] = None

class ModuleSchema(BaseModel):
    type: str = Field(pattern='^module$')
    info: InfoBlock = Field(alias="metadata")
    vars: Dict[str, VarConfig] = {}
    steps: List[ModuleStep] = []

# --- Workflow Specific ---

class WorkflowStep(BaseModel):
    name: str
    module: str
    depends_on: List[str] = []
    inputs: Dict[str, Any] = {}

class WorkflowSchema(BaseModel):
    type: str = Field(pattern='^workflow$')
    info: InfoBlock = Field(alias="metadata")
    vars: Dict[str, VarConfig] = {}
    workflow: List[WorkflowStep] = []

# --- Validator Function ---

def validate_yaml(data: dict) -> Union[ModuleSchema, WorkflowSchema]:
    """
    Validates dictionary data against Module or Workflow schema based on 'type'.
    """
    if 'type' not in data:
        raise ValueError("Missing 'type' field in YAML.")
    
    if data['type'] == 'module':
        return ModuleSchema(**data)
    elif data['type'] == 'workflow':
        return WorkflowSchema(**data)
    else:
        raise ValueError(f"Unknown type: {data['type']}")
