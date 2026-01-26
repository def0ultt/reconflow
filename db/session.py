from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.paths import get_project_root
from .models import Base

def get_db_url():
    root = get_project_root()
    db_path = root / "reconflow.db"
    return f"sqlite:///{db_path}"

_engine = None
_SessionLocal = None

def init_db():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(
            get_db_url(), 
            connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=_engine)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

def get_session():
    """
    Return a new database session.
    """
    if _SessionLocal is None:
        init_db()
    return _SessionLocal()
