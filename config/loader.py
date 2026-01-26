import yaml
from pathlib import Path
from .schemas import Config
from utils.paths import get_project_root

def load_config(path: str = None) -> Config:
    """
    Load configuration from YAML file.
    """
    if path is None:
        path = get_project_root() / "config" / "defaults.yml"
    
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return Config(**data)
    except FileNotFoundError:
        # Fallback to default
        return Config()
    except Exception as e:
        print(f"Error loading config: {e}")
        return Config()
