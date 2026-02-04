from typing import Dict, Any, List
from pydantic import BaseModel

class Option(BaseModel):
    name: str
    value: Any = None
    required: bool = True
    description: str = ""
    metadata: Dict[str, Any] = {}  # Store type, flag, etc.

class BaseModule:
    """
    Base class for all ReconFlow modules.
    """
    meta = {
        'name': 'Unknown Module',
        'description': '',
        'author': 'Unknown',
        'version': '1.0'
    }

    options: Dict[str, Option] = {}

    def __init__(self):
        # Deep copy options to avoid shared state issues between instances if any
        self.options = {k: v.model_copy() for k, v in self.options.items()}

    def update_option(self, key: str, value: str):
        if key in self.options:
            self.options[key].value = value
            return True
        return False

    def validate_options(self) -> List[str]:
        missing = []
        for key, opt in self.options.items():
            if opt.required and not opt.value:
                # Basic check, can be improved
                if opt.value is None or opt.value == "":
                     missing.append(key)
        return missing

    def run(self, context, background=False):
        raise NotImplementedError
