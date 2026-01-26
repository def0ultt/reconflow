import os
from pathlib import Path

def get_project_root() -> Path:
    """
    Return the project root directory (reconflow/).
    """
    # Assuming this file is in utils/paths.py, so root is two levels up
    return Path(__file__).parent.parent

def ensure_dir(path: Path):
    """
    Ensure a directory exists.
    """
    path.mkdir(parents=True, exist_ok=True)

def get_results_dir() -> Path:
    """Return the global results directory."""
    root = get_project_root()
    results_dir = root / "results"
    ensure_dir(results_dir)
    return results_dir
