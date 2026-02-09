from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator

# --- Shared Components ---

class InfoBlock(BaseModel):
    id: str
    name: str = "Unknown"
    tag: str = ""
    author: str = "Unknown"
    description: str = ""
    
    @field_validator('id')
    @classmethod
    def validate_id_no_whitespace(cls, v):
        """Ensure ID doesn't contain any whitespace characters"""
        if ' ' in v or '\t' in v or '\n' in v or '\r' in v:
            raise ValueError(f"Module ID cannot contain whitespace characters. Got: '{v}'")
        return v

class VarConfig(BaseModel):
    type: str = "string"  # "string" or "boolean"
    default: Optional[Any] = None
    required: bool = False
    flag: Optional[str] = None  # CLI flag for boolean variables
    description: Optional[str] = None # Description of the variable
    
    @model_validator(mode='after')
    def validate_boolean_config(self):
        """Validate boolean variable configuration"""
        if self.type == "boolean":
            # Validate default is boolean or None
            if self.default is not None and not isinstance(self.default, bool):
                raise ValueError(f"Boolean variable must have boolean default, got {type(self.default).__name__}")
        elif self.type != "string":
            raise ValueError(f"Variable type must be 'string' or 'boolean', got '{self.type}'")
        
        # Only boolean variables can have flags
        if self.flag and self.type != "boolean":
            raise ValueError("Only boolean variables can have a 'flag' field")
        
        return self

class OutputConfig(BaseModel):
    path: Optional[str] = None
    filename: Optional[str] = None

# --- Unified Module Schema ---

class ModuleStep(BaseModel):
    name: str
    tool: Optional[str] = None
    module: Optional[str] = None
    args: str = ""
    capture: bool = False
    stdin: bool = False
    timeout: Optional[str] = None
    condition: Optional[str] = None
    output: Optional[OutputConfig] = None
    depends_on: List[str] = Field(default_factory=list)
    parallel: bool = True
    path: Optional[str] = None  # Custom path for tool execution
    filename: Optional[str] = None # Output filename (supports conditionals)

    @model_validator(mode='after')
    def check_tool_or_module(self):
        if not self.tool and not self.module:
            raise ValueError("Step must specify either 'tool' or 'module'.")
        if self.tool and self.module:
            raise ValueError("Step cannot specify both 'tool' and 'module'.")
        return self

class ModuleSchema(BaseModel):
    type: str = Field(pattern='^module$')
    info: InfoBlock = Field(alias="metadata", validation_alias="info") # Allow 'info' as alias for metadata
    vars: Dict[str, VarConfig] = {}
    steps: List[ModuleStep] = []

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v != 'module':
            raise ValueError("Type must be 'module'")
        return v

# --- Validator Function ---

def validate_yaml(data: dict) -> ModuleSchema:
    """
    Validates dictionary data against Module schema.
    Workflows are now Modules.
    """
    if 'type' not in data:
        raise ValueError("Missing 'type' field in YAML.")
    
    if data['type'] == 'module':
        # Backward compatibility for 'info' field if pydantic alias doesn't catch it automatically in all versions
        # But 'alias' in Field usually handles dict keys. 
        # In Pydantic V2 'validation_alias' is preferred for input data mapping.
        # We used validation_alias="info" above.
        return ModuleSchema(**data)
    else:
        raise ValueError(f"Unknown or unsupported type: {data['type']}. Only 'module' is supported.")
