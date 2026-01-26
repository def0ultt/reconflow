from pydantic import BaseModel
from typing import Optional

class AppConfig(BaseModel):
    name: str = "ReconFlow"
    version: str = "0.1.0"

class Config(BaseModel):
    """
    Main configuration schema.
    """
    app: AppConfig = AppConfig()
    # Add other sections as needed (e.g. tools_path, db_url)
