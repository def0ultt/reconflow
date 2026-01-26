import subprocess
import shlex

class Runner:
    """
    Handles subprocess or asyncio execution of commands.
    """
    def run_command(self, cmd: str):
        """Run a shell command."""
        try:
            # For security, one should be careful with shell=True, but for this tool user input is expected.
            # Splitting args is safer if not using shell=True
            args = shlex.split(cmd)
            result = subprocess.run(args, capture_output=True, text=True)
            return result.stdout, result.stderr
        except Exception as e:
            return "", str(e)
