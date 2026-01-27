import threading
import time
from datetime import datetime
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from db.models import SessionModel, Workspace
from db.session import get_session
from core.base import BaseModule

class SessionManager:
    def __init__(self):
        self.active_sessions: Dict[int, threading.Thread] = {}
        self.session_map: Dict[int, int] = {} # Map DB ID to Thread Ident (optional) or just track by DB ID

    def create_session(self, module: BaseModule, context, target: str) -> Optional[SessionModel]:
        """
        Creates a new session in the DB and starts the module in a background thread.
        """
        if not context.current_workspace:
            print("❌ No active workspace. Cannot create session.")
            return None

        # Create DB Entry
        db: Session = get_session()
        try:
            new_session = SessionModel(
                workspace_id=context.current_workspace.id,
                module=module.meta['name'],
                target=target,
                status="running",
                start_time=datetime.utcnow()
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            session_id = new_session.id
        except Exception as e:
            print(f" Failed to create session in DB: {e}")
            db.rollback()
            return None
        finally:
            db.close()

        # Define wrapper for thread
        def run_wrapper(sess_id, mod, ctx):
            # Update status logic could go here
            try:
                mod.run(ctx)
                self._update_status(sess_id, "completed")
            except Exception as e:
                print(f"Session {sess_id} failed: {e}")
                self._update_status(sess_id, "failed", info=str(e))

        # Start Thread
        t = threading.Thread(target=run_wrapper, args=(session_id, module, context), daemon=True)
        self.active_sessions[session_id] = t
        t.start()
        
        return new_session

    def _update_status(self, session_id: int, status: str, info: str = None):
        db: Session = get_session()
        try:
            sess = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if sess:
                sess.status = status
                if status in ["completed", "failed", "stopped"]:
                    sess.end_time = datetime.utcnow()
                if info:
                    sess.info = info
                db.commit()
        except Exception as e:
            print(f" Error updating session {session_id}: {e}")
        finally:
            db.close()
            # Clean up active_sessions if finished
            if status in ["completed", "failed", "stopped"] and session_id in self.active_sessions:
                del self.active_sessions[session_id]

    def list_sessions(self, workspace_id: int = None) -> List[SessionModel]:
        db: Session = get_session()
        try:
            query = db.query(SessionModel)
            if workspace_id:
                query = query.filter(SessionModel.workspace_id == workspace_id)
            return query.all()
        finally:
            db.close()

    def stop_session(self, session_id: int) -> bool:
        if session_id in self.active_sessions:
            # Thread killing is hard in Python. 
            # Ideally modules should check a 'stop' flag.
            # For now, we just mark it as stopped in DB and remove from active list.
            # The thread might continue running until completion.
            self._update_status(session_id, "stopped")
            return True
        return False
