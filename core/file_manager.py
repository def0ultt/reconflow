import os
import shutil
from pathlib import Path
from db.repositories.project_repo import ProjectRepository
from db.models.project import Project

class FileManager:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    def save_tool_output(self, project: Project, tool_name: str, content: str | bytes, original_filename: str, subdir: str = None):
        """
        Saves tool output to the project directory (optionally inside a subdir) and records it in the database.
        Enforces creation of a .txt copy.
        """
        project_path = Path(project.path)
        if subdir:
            project_path = project_path / subdir
            
        if not project_path.exists():
            project_path.mkdir(parents=True, exist_ok=True)

        original_file_path = project_path / original_filename
        
        # Save validation
        mode = 'wb' if isinstance(content, bytes) else 'w'
        with open(original_file_path, mode) as f:
            f.write(content)

        # Get stats
        size = original_file_path.stat().st_size
        
        # Add to DB
        self.project_repo.add_file_record(
            project_id=project.id,
            tool_name=tool_name,
            file_path=str(original_file_path.absolute()),
            file_size_bytes=size
        )
        print(f"Saved {original_file_path} (Size: {size})")

        # "Always TXT" Rule
        if original_file_path.suffix != '.txt':
             txt_filename = original_file_path.stem + ".txt"
             txt_file_path = project_path / txt_filename
             
             # If content is bytes, try to decode, otherwise standard save
             txt_content = content
             if isinstance(content, bytes):
                 try:
                     txt_content = content.decode('utf-8')
                 except UnicodeDecodeError:
                     txt_content = f"[Binary data converted to string repr]: {str(content)}"
            
             with open(txt_file_path, 'w') as f:
                 f.write(txt_content)
            
             size_txt = txt_file_path.stat().st_size
             self.project_repo.add_file_record(
                project_id=project.id,
                tool_name=tool_name,
                file_path=str(txt_file_path.absolute()),
                file_size_bytes=size_txt
             )
             print(f"Saved .txt copy {txt_file_path}")

    def get_file_content(self, project_id: int, filename: str) -> str | None:
        """
        Retrieves file content for a given filename in a project.
        Supports full filename (path relative to project?) or just basename.
        """
        # Get project to know root
        project = self.project_repo.get(project_id)
        if not project:
            return None
            
        all_files = self.project_repo.get_files(project_id)
        target_record = None
        
        # Strategy 1: Treat filename as relative path from project root
        # This is the most likely intent for "cat workflow/scan.txt"
        try:
            potential_abs_path = (Path(project.path) / filename).resolve()
            # Search for this specific path in records
            for f in all_files:
                if Path(f.file_path).resolve() == potential_abs_path:
                    target_record = f
                    break
        except Exception:
            pass
            
        # Strategy 2: Ends-with match (Partial path)
        if not target_record:
            for f in all_files:
                if f.file_path.endswith(filename):
                     target_record = f
                     break
        
        # Strategy 3: Basename (if filename has no path separators)
        if not target_record and '/' not in filename and '\\' not in filename:
             target_record = self.project_repo.get_file_by_name(project_id, filename)

        if target_record:
            if os.path.exists(target_record.file_path):
                try:
                    with open(target_record.file_path, 'r') as f:
                        return f.read()
                except UnicodeDecodeError:
                    return "[Error: Binary file, cannot display in terminal]"
        return None
