from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..base import Base

class Variable(Base):
    __tablename__ = 'variables'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, index=True) # e.g., "$target"
    value = Column(String, nullable=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True) # Null = Global
    
    # Relationships
    project = relationship("Project", back_populates="variables")

    # Ensure unique key per scope (global or per project)
    # Actually, SQLite unique constraints with NULL can be tricky, but typical UniqueConstraint works if DB supports it.
    # We enforce logic in app level if needed.
    # __table_args__ = (UniqueConstraint('key', 'project_id', name='_key_project_uc'),) 
    
    def __repr__(self):
        scope = f"Project({self.project_id})" if self.project_id else "Global"
        return f"<Variable({self.key}={self.value}, scope={scope})>"
