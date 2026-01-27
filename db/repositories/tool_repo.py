from sqlalchemy.orm import Session
from .base_repo import BaseRepository
from ..models.tool import Tool

class ToolRepository(BaseRepository[Tool]):
    def __init__(self, session: Session):
        super().__init__(Tool, session)

    def get_by_name(self, name: str) -> Tool | None:
        return self.session.query(Tool).filter(Tool.name == name).first()
