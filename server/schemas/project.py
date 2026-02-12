from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    path: Optional[str] = None

class ProjectCreate(ProjectBase):
    is_temp: bool = False

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    description: Optional[str] = None

class ProjectStats(BaseModel):
    file_count: int = 0
    total_size_bytes: int = 0
    last_modified: Optional[datetime] = None

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    # path is required in response
    path: str
    stats: Optional[ProjectStats] = None

    class Config:
        from_attributes = True
