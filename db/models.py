from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    path = Column(String, nullable=False)

    scans = relationship("ScanResult", back_populates="project")

class ScanResult(Base):
    __tablename__ = 'scan_results'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    tool_name = Column(String)
    target = Column(String)
    output_file = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="scans")
