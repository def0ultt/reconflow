from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from ..base import Base


class Tool(Base):
    __tablename__ = 'tools'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    command_template = Column(String, nullable=True)  # e.g. "nmap -sV {target}"
    is_active = Column(Boolean, default=True)

    # Tool Profile Fields
    binary_path = Column(String, nullable=True)       # /usr/bin/subfinder
    default_args = Column(Text, nullable=True)        # JSON: ["-silent", "-o", "{{output}}"]
    category = Column(String, nullable=True, index=True)  # recon, scanning, bruteforce, etc.
    tags = Column(Text, nullable=True)                # JSON: ["subdomain", "passive"]
    inputs = Column(Text, nullable=True)              # JSON: [{name, type, required, description}]
    outputs = Column(Text, nullable=True)             # JSON: [{name, type, description}]
    icon = Column(String, nullable=True)              # Icon identifier
    author = Column(String, default='user')           # 'user' or 'builtin'

    # Tool can be part of many workflow modules
    modules = relationship("WorkflowModuleTool", back_populates="tool")

    def __repr__(self):
        return f"<Tool(name={self.name})>"
