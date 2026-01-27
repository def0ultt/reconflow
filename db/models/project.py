from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..base import Base

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # The physical path where output tools save their results (e.g., /home/scan)
    path = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    scans = relationship("ScanResult", back_populates="project", cascade="all, delete-orphan")
    sessions = relationship("SessionModel", back_populates="project", cascade="all, delete-orphan")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(name={self.name}, path={self.path})>"

class ProjectFile(Base):
    __tablename__ = 'project_files'
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    tool_name = Column(String, index=True)
    file_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="files")

    def __repr__(self):
        return f"<ProjectFile(path={self.file_path})>"

class ScanResult(Base):
    __tablename__ = 'scan_results'
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    tool_name = Column(String, index=True)
    target = Column(String, index=True)
    output_file = Column(String) # Path to specific output file
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String) # SUCCESS, FAILURE
    
    project = relationship("Project", back_populates="scans")

class SessionModel(Base):
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    module = Column(String) # Which module is running
    target = Column(String)
    status = Column(String) # running, completed, stopped, failed
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    info = Column(Text, nullable=True) # Arbitrary info or logs
    
    project = relationship("Project", back_populates="sessions")
