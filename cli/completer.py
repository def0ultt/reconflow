from prompt_toolkit.completion import WordCompleter
from .commands import COMMANDS

class Completer:
    """
    Autocomplete logic for the CLI.
    """
    def __init__(self):
        self.completer = WordCompleter(
            list(COMMANDS.keys()) + ['exit'],
            ignore_case=True,
            sentence=True
        )
    
    def get_completer(self):
        return self.completer
