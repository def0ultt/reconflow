from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from ..base import Base

class APIKey(Base):
    __tablename__ = 'api_keys'

    id = Column(Integer, primary_key=True, index=True)
    tool_name = Column(String, unique=True, nullable=False, index=True) # e.g., "amass", "subfinder"
    key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<APIKey(tool={self.tool_name})>"
