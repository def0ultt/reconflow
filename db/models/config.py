from sqlalchemy import Column, Integer, String, Boolean
from ..base import Base

class Config(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(String, nullable=True)
    is_encrypted = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Config(key={self.key})>"
