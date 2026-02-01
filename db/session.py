from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from utils.paths import get_project_root
from .base import Base
# Import all models so they are registered with Base.metadata.create_all()
from .models import * 

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
            connect_args={"check_same_thread": False} # Needed for SQLite
        )
        # Create all tables
        Base.metadata.create_all(bind=_engine)
        
        # Use scoped_session for thread safety
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        _SessionLocal = scoped_session(session_factory)

def get_session():
    """
    Return a new database session.
    """
    if _SessionLocal is None:
        init_db()
    return _SessionLocal()

def create_new_session():
    """
    Return a fresh, non-scoped session.
    Useful for background threads to avoid closing the main scoped session.
    """
    if _engine is None:
        init_db()
    
    Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return Session()

@contextmanager
def db_session():
    """
    Context manager for database sessions.
    Usage:
        with db_session() as session:
            session.query(...)
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
