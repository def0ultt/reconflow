from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import os
import re
import json
import fnmatch
from pathlib import Path
from db import models
from db.session import get_session
from projects.manager import ProjectManager

router = APIRouter()

def get_project_manager():
    return ProjectManager()


def _get_project_path(project_id: int, manager: ProjectManager) -> Path:
    """Helper to get and validate project path."""
    project = manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_path = Path(project.path)
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project directory not found")
    return project_path


@router.get("/{project_id}/artifacts")
def list_artifacts(project_id: int, manager: ProjectManager = Depends(get_project_manager)):
    """List all artifacts (files) in the project directory."""
    project = manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_path = Path(project.path)
    if not project_path.exists():
        return []

    artifacts = []
    for root, dirs, files in os.walk(project_path):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(project_path)

            if file.startswith('.'):
                continue

            artifacts.append({
                "name": file,
                "path": str(rel_path),
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime,
                "type": file_path.suffix.lower().lstrip('.') or 'unknown'
            })

    return artifacts


def _parse_file_to_rows(file_path: Path):
    """
    Parse a file into rows + columns for table display.
    Supports: .json, .jsonl, .txt, .log, .csv, .md, .yml, .yaml
    Returns (columns, rows) tuple.
    """
    suffix = file_path.suffix.lower()

    try:
        # JSON array
        if suffix == '.json':
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = json.load(f)
            if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
                columns = list(dict.fromkeys(k for row in content[:50] for k in row.keys()))
                return columns, content
            elif isinstance(content, dict):
                return list(content.keys()), [content]
            else:
                return ["value"], [{"value": str(item)} for item in content] if isinstance(content, list) else [{"value": str(content)}]

        # JSONL (one JSON object per line)
        if suffix == '.jsonl':
            rows = []
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict):
                            rows.append(obj)
                        else:
                            rows.append({"value": str(obj)})
                    except json.JSONDecodeError:
                        rows.append({"value": line})
            if rows:
                columns = list(dict.fromkeys(k for row in rows[:50] for k in (row.keys() if isinstance(row, dict) else ["value"])))
            else:
                columns = ["value"]
            return columns, rows

        # Plain text files → one column per line
        if suffix in ['.txt', '.log', '.md', '.csv', '.yml', '.yaml', '']:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.read().splitlines()
            return ["value"], [{"value": line} for line in lines if line.strip()]

        # Unsupported binary
        return [], []

    except Exception:
        return [], []


@router.get("/{project_id}/artifacts/{file_path:path}")
def get_artifact_content(project_id: int, file_path: str, manager: ProjectManager = Depends(get_project_manager)):
    """Get parsed content of a specific artifact for table display."""
    project = manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_root = Path(project.path).resolve()
    target_path = (project_root / file_path).resolve()

    # Security: path traversal check
    if not str(target_path).startswith(str(project_root)):
        raise HTTPException(status_code=403, detail="Access denied: Path traversal detected")

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    columns, rows = _parse_file_to_rows(target_path)

    if not columns and not rows:
        return {"type": "binary", "message": "Binary file — content not displayed"}

    return {
        "type": "table",
        "columns": columns,
        "rows": rows,
        "total_count": len(rows)
    }


@router.get("/{project_id}/search")
def search_artifacts(
    project_id: int,
    q: str = Query(..., min_length=1, description="Search query"),
    regex: bool = Query(False, description="Treat query as regex"),
    include: Optional[str] = Query(None, description="Comma-separated glob patterns to include"),
    exclude: Optional[str] = Query(None, description="Comma-separated glob patterns to exclude"),
    manager: ProjectManager = Depends(get_project_manager)
):
    """
    Search across all project files (like grep -R).
    Returns matches grouped by file.
    """
    project = manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_path = Path(project.path)
    if not project_path.exists():
        return {"total_matches": 0, "results": []}

    include_patterns = [p.strip() for p in include.split(",")] if include else None
    exclude_patterns = [p.strip() for p in exclude.split(",")] if exclude else None

    # Compile search pattern
    if regex:
        try:
            pattern = re.compile(q, re.IGNORECASE)
        except re.error as e:
            raise HTTPException(status_code=400, detail=f"Invalid regex: {str(e)}")
    else:
        pattern = re.compile(re.escape(q), re.IGNORECASE)

    results = []
    total_matches = 0

    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.startswith('.'):
                continue

            # Apply include/exclude filters
            if include_patterns and not any(fnmatch.fnmatch(file, p) for p in include_patterns):
                continue
            if exclude_patterns and any(fnmatch.fnmatch(file, p) for p in exclude_patterns):
                continue

            file_path = Path(root) / file
            rel_path = str(file_path.relative_to(project_path))

            # Only search text-like files
            suffix = file_path.suffix.lower()
            if suffix in ['.bin', '.exe', '.png', '.jpg', '.gif', '.zip', '.gz', '.tar', '.pdf']:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    matches = []
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            matches.append({
                                "line_number": line_num,
                                "content": line.rstrip('\n')[:500]  # Cap line length
                            })
                            if len(matches) >= 200:  # Cap matches per file
                                break

                if matches:
                    total_matches += len(matches)
                    results.append({
                        "file": rel_path,
                        "match_count": len(matches),
                        "matches": matches
                    })
            except Exception:
                continue

    # Sort by match count descending
    results.sort(key=lambda r: r["match_count"], reverse=True)

    return {
        "total_matches": total_matches,
        "results": results
    }
