from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..base import Base

class Workflow(Base):
    __tablename__ = 'workflows'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    modules = relationship("WorkflowModule", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowModule.order")

    def __repr__(self):
        return f"<Workflow(name={self.name})>"

class WorkflowModule(Base):
    __tablename__ = 'workflow_modules'

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id'))
    name = Column(String, nullable=False) # e.g. "Recon", "Scanning"
    order = Column(Integer, default=0) # Execution order
    
    workflow = relationship("Workflow", back_populates="modules")
    tools = relationship("WorkflowModuleTool", back_populates="module", cascade="all, delete-orphan", order_by="WorkflowModuleTool.order")

    def __repr__(self):
        return f"<WorkflowModule(name={self.name}, order={self.order})>"

class WorkflowModuleTool(Base):
    __tablename__ = 'workflow_module_tools'

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey('workflow_modules.id'))
    tool_id = Column(Integer, ForeignKey('tools.id'))
    order = Column(Integer, default=0)
    
    # Specific arguments for this tool in this workflow context
    arguments = Column(String, nullable=True) 

    module = relationship("WorkflowModule", back_populates="tools")
    tool = relationship("Tool", back_populates="modules")

    def __repr__(self):
        return f"<WorkflowModuleTool(module_id={self.module_id}, tool_id={self.tool_id})>"
