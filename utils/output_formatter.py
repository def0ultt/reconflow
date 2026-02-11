"""
Professional output formatting utilities for ReconFlow CLI.
Provides consistent, colored, and user-friendly output formatting.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import Optional

import sys
from typing import List, Callable

class SplitStream:
    """
    Splits stdout to original stream and registered listeners.
    Used to capture CLI output for WebSockets.
    """
    def __init__(self, original_stream):
        self.original = original_stream
        self.listeners: List[Callable[[str], None]] = []

    def write(self, text):
        try:
            self.original.write(text)
            for listener in self.listeners:
                try:
                    listener(text)
                except:
                    pass
        except:
            pass
            
    def flush(self):
        try:
            self.original.flush()
        except:
            pass
            
    def add_listener(self, callback: Callable[[str], None]):
        self.listeners.append(callback)

    def remove_listener(self, callback: Callable[[str], None]):
        if callback in self.listeners:
            self.listeners.remove(callback)

# Initialize console with split stream
stdout_stream = SplitStream(sys.stdout)
console = Console(file=stdout_stream, force_terminal=True, color_system="truecolor")


def format_tool_execution(step_name: str, tool: str, command: str):
    """
    Format tool execution message.
    
    Args:
        step_name: Name of the step
        tool: Tool being executed
        command: Full command being run
    """
    console.print(f"\n🔧 [bold cyan]Running:[/bold cyan] [yellow]{tool}[/yellow]")
    console.print(f"   [dim]Command: {command}[/dim]")


def format_output_saved(path: str):
    """
    Format output saved confirmation.
    
    Args:
        path: Path where output was saved
    """
    console.print(f"   💾 [green]Saved →[/green] [dim]{path}[/dim]")


def format_error(title: str, reason: str, suggestion: Optional[str] = None):
    """
    Format professional error message with fix suggestions.
    
    Args:
        title: Error title
        reason: Reason for the error
        suggestion: Optional fix suggestion
    """
    error_text = f"[bold red]❌ {title}[/bold red]\n\n"
    error_text += f"[yellow]Reason:[/yellow] {reason}\n"
    
    if suggestion:
        error_text += f"\n[cyan]💡 Fix:[/cyan] {suggestion}"
    
    panel = Panel(
        error_text,
        border_style="red",
        padding=(1, 2)
    )
    console.print("\n")
    console.print(panel)
    console.print()


def format_success(message: str):
    """
    Format success message.
    
    Args:
        message: Success message to display
    """
    console.print(f"\n✅ [bold green]{message}[/bold green]\n")


def format_warning(message: str):
    """
    Format warning message.
    
    Args:
        message: Warning message to display
    """
    console.print(f"⚠️  [yellow]{message}[/yellow]")


def format_step_skipped(step_name: str, condition: str):
    """
    Format step skipped message.
    
    Args:
        step_name: Name of the skipped step
        condition: Condition that caused the skip
    """
    console.print(f"   ⏭️  [dim]Skipped '{step_name}' (condition: {condition})[/dim]")


def indent_output(text: str, level: int = 1) -> str:
    """
    Indent text output for better readability.
    
    Args:
        text: Text to indent
        level: Indentation level (default: 1)
    
    Returns:
        Indented text
    """
    indent = "   " * level
    lines = text.split('\n')
    return '\n'.join(f"{indent}{line}" for line in lines)


def get_error_suggestion(error_type: str, context: dict) -> Optional[str]:
    """
    Get contextual error fix suggestions.
    
    Args:
        error_type: Type of error
        context: Error context information
    
    Returns:
        Fix suggestion or None
    """
    suggestions = {
        'command_not_found': lambda ctx: f"Install {ctx.get('tool', 'the tool')} or check if it's in your PATH",
        'file_not_found': lambda ctx: f"Verify the file path exists: {ctx.get('path', '')}",
        'timeout': lambda ctx: f"Increase timeout value or optimize the command",
        'permission_denied': lambda ctx: f"Check file permissions or run with appropriate privileges",
        'template_error': lambda ctx: f"Check variable '{ctx.get('var', '')}' is defined in vars section",
    }
    
    suggestion_fn = suggestions.get(error_type)
    return suggestion_fn(context) if suggestion_fn else None


def format_command_error(step_name: str, error: Exception, command: str):
    """
    Format command execution error with intelligent suggestions.
    
    Args:
        step_name: Name of the step that failed
        error: Exception that occurred
        command: Command that failed
    """
    error_str = str(error)
    
    # Detect error type and provide suggestions
    if "returned non-zero exit status 127" in error_str or "command not found" in error_str.lower():
        # Extract tool name from command
        tool = command.split()[0] if command else "unknown"
        format_error(
            title=f"Command Not Found in '{step_name}'",
            reason=f"Tool '{tool}' is not installed or not in PATH",
            suggestion=f"Install {tool} or verify it's available:\n   which {tool}"
        )
    elif "returned non-zero exit status 126" in error_str:
        format_error(
            title=f"Permission Denied in '{step_name}'",
            reason="Command exists but cannot be executed",
            suggestion="Check file permissions:\n   chmod +x <file>"
        )
    elif "timed out" in error_str.lower():
        format_error(
            title=f"Timeout in '{step_name}'",
            reason="Command execution exceeded timeout limit",
            suggestion="Increase timeout in module definition:\n   timeout: \"30m\""
        )
    elif "No such file or directory" in error_str:
        format_error(
            title=f"File Not Found in '{step_name}'",
            reason="Required file or directory does not exist",
            suggestion="Verify all file paths in the command are correct"
        )
    else:
        # Generic error
        format_error(
            title=f"Execution Failed in '{step_name}'",
            reason=error_str,
            suggestion="Check the command syntax and arguments"
        )


def format_deadlock_error(pending_steps: list, failed_steps: set):
    """
    Format deadlock/dependency failure error.
    
    Args:
        pending_steps: List of pending steps
        failed_steps: Set of failed steps
    """
    error_text = "[bold red]❌ Execution Deadlock Detected[/bold red]\n\n"
    
    if failed_steps:
        error_text += f"[yellow]Failed Steps:[/yellow] {', '.join(failed_steps)}\n"
    
    if pending_steps:
        error_text += f"[yellow]Blocked Steps:[/yellow] {', '.join(pending_steps)}\n"
    
    error_text += "\n[cyan]💡 Fix:[/cyan] Check step dependencies and ensure failed steps are not required"
    
    panel = Panel(
        error_text,
        border_style="red",
        padding=(1, 2)
    )
    console.print("\n")
    console.print(panel)
    console.print()
