from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..base import Base

class Tool(Base):
    __tablename__ = 'tools'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True) # e.g. "nmap", "amass"
    description = Column(Text, nullable=True)
    command_template = Column(String, nullable=True) # e.g. "nmap -sV {target}"
    is_active = Column(Boolean, default=True)
    
    # Tool can be part of many workflow modules
    modules = relationship("WorkflowModuleTool", back_populates="tool")

    def __repr__(self):
        return f"<Tool(name={self.name})>"
