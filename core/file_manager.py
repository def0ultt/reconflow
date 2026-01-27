import os
import shutil
from pathlib import Path
from db.repositories.project_repo import ProjectRepository
from db.models.project import Project

class FileManager:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    def save_tool_output(self, project: Project, tool_name: str, content: str | bytes, original_filename: str):
        """
        Saves tool output to the project directory and records it in the database.
        Enforces creation of a .txt copy.
        """
        project_path = Path(project.path)
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
            
             # Record TXT version too? User said "Save a copy... insert a new row".
             # Usually we want the TXT version accessible via CLI "show files". 
             # So yes, we record it.
             
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
        """
        file_record = self.project_repo.get_file_by_name(project_id, filename)
        if file_record:
            if os.path.exists(file_record.file_path):
                try:
                    with open(file_record.file_path, 'r') as f:
                        return f.read()
                except UnicodeDecodeError:
                    return "[Error: Binary file, cannot display in terminal]"
        return None
