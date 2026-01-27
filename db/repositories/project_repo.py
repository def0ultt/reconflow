from sqlalchemy.orm import Session
from .base_repo import BaseRepository
from ..models.project import Project, ScanResult, SessionModel, ProjectFile
import os

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: Session):
        super().__init__(Project, session)

    def get_by_name(self, name: str) -> Project | None:
        return self.session.query(Project).filter(Project.name == name).first()

    def create_project(self, name: str, path: str, description: str = None) -> Project:
        # Ensure path exists or create it? 
        # User said: "it also takes a save output tools in path provide by user example/home/scan .when he create new project"
        # We assume logic to create directory might be here or in service layer. 
        # For a repository, we generally just store data, but we can validate.
        
        project = self.get_by_name(name)
        if project:
            raise ValueError(f"Project with name {name} already exists.")
        
        return self.create({"name": name, "path": path, "description": description})

    def add_file_record(self, project_id: int, tool_name: str, file_path: str, file_size_bytes: int) -> ProjectFile:
        file_record = ProjectFile(
            project_id=project_id,
            tool_name=tool_name,
            file_path=file_path,
            file_size_bytes=file_size_bytes
        )
        self.session.add(file_record)
        self.session.commit()
        self.session.refresh(file_record)
        return file_record

    def get_files(self, project_id: int) -> list[ProjectFile]:
        return self.session.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()

    def get_file_by_name(self, project_id: int, filename: str) -> ProjectFile | None:
        # Assuming filename is the basename or we search by path suffix?
        # User said: "Command show [filename] ... search SQLite for the specific filename"
        # We'll assume strict match on basename for now, or partial match on path.
        # Let's try to match basename first.
        all_files = self.get_files(project_id)
        for f in all_files:
            if os.path.basename(f.file_path) == filename:
                return f
        return None

    def add_scan_result(self, project_id: int, tool_name: str, target: str, output_file: str, status: str = "SUCCESS"):
        scan = ScanResult(
            project_id=project_id,
            tool_name=tool_name,
            target=target,
            output_file=output_file,
            status=status
        )
        self.session.add(scan)
        self.session.commit()
        self.session.refresh(scan)
        return scan

    def create_session(self, project_id: int, module: str, target: str) -> SessionModel:
        session_obj = SessionModel(
            project_id=project_id,
            module=module,
            target=target,
            status="running"
        )
        self.session.add(session_obj)
        self.session.commit()
        self.session.refresh(session_obj)
        return session_obj
