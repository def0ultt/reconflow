from pydantic import BaseModel, Field
from typing import Optional, List


class ToolIOSchema(BaseModel):
    name: str
    type: str = "string"  # "string", "file", "list"
    required: bool = False
    description: Optional[str] = None


class ToolCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    binary_path: Optional[str] = None
    command_template: Optional[str] = None
    default_args: List[str] = []
    category: Optional[str] = None
    tags: List[str] = []
    inputs: List[ToolIOSchema] = []
    outputs: List[ToolIOSchema] = []
    icon: Optional[str] = None


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    binary_path: Optional[str] = None
    command_template: Optional[str] = None
    default_args: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    inputs: Optional[List[ToolIOSchema]] = None
    outputs: Optional[List[ToolIOSchema]] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class ToolResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    binary_path: Optional[str] = None
    command_template: Optional[str] = None
    default_args: List[str] = []
    category: Optional[str] = None
    tags: List[str] = []
    inputs: List[ToolIOSchema] = []
    outputs: List[ToolIOSchema] = []
    icon: Optional[str] = None
    author: Optional[str] = "user"
    is_active: bool = True

    class Config:
        from_attributes = True
