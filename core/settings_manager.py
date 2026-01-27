from db.session import get_session
from db.models.api_key import APIKey
from db.models.variable import Variable
from db.models.project import Project
from sqlalchemy.orm import Session

class SettingsManager:
    def __init__(self, session: Session = None):
        self.session = session or get_session()

    # --- API Keys ---
    def get_api_key(self, tool_name: str) -> str | None:
        key_obj = self.session.query(APIKey).filter_by(tool_name=tool_name).first()
        return key_obj.key if key_obj else None

    def set_api_key(self, tool_name: str, key: str):
        existing = self.session.query(APIKey).filter_by(tool_name=tool_name).first()
        if existing:
            existing.key = key
        else:
            self.session.add(APIKey(tool_name=tool_name, key=key))
        self.session.commit()

    def list_api_keys(self):
        return self.session.query(APIKey).all()

    # --- Variables ---
    def set_variable(self, key: str, value: str, project_id: int = None):
        """
        Set a variable. 
        If project_id is None, it's global.
        If project_id is set, it's specific.
        Key must start with $.
        """
        if not key.startswith('$'):
            raise ValueError("Variable name must start with $")

        existing = self.session.query(Variable).filter_by(key=key, project_id=project_id).first()
        if existing:
            existing.value = value
        else:
            self.session.add(Variable(key=key, value=value, project_id=project_id))
        self.session.commit()

    def get_variable(self, key: str, project_id: int = None) -> str | None:
        """
        Get variable.
        Priority: Project-specific > Global
        If project_id is provided, checks specific first, then global.
        """
        if project_id:
            specific = self.session.query(Variable).filter_by(key=key, project_id=project_id).first()
            if specific:
                return specific.value
        
        # Fallback to global
        global_var = self.session.query(Variable).filter_by(key=key, project_id=None).first()
        return global_var.value if global_var else None

    def delete_variable(self, key: str, project_id: int = None) -> bool:
        """
        Delete a variable.
        Returns True if deleted, False if not found.
        """
        existing = self.session.query(Variable).filter_by(key=key, project_id=project_id).first()
        if existing:
            self.session.delete(existing)
            self.session.commit()
            return True
        return False

    def list_variables(self, project_id: int = None, include_all: bool = False):
        """
        List variables.
        If include_all is True, returns EVERYTHING (Global + All Projects).
        If project_id is provided, lists global + that project's specifics.
        If project_id None and include_all False, lists only global.
        """
        query = self.session.query(Variable)
        if include_all:
             return query.all()
        elif project_id:
            return query.filter((Variable.project_id == None) | (Variable.project_id == project_id)).all()
        else:
            return query.filter(Variable.project_id == None).all()
