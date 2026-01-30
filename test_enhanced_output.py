"""
Test script to verify enhanced professional CLI output.
Tests colored progress, tool names, and error formatting.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.progress import ProgressTracker
from utils.output_formatter import (
    format_tool_execution,
    format_output_saved,
    format_error,
    format_success,
    format_warning,
    console
)

def test_progress_with_tools():
    """Test progress tracker with tool names and colors."""
    print("=" * 60)
    console.print("[bold cyan]Testing Enhanced Progress Display[/bold cyan]")
    print("=" * 60)
    print()
    
    tools = ["subfinder", "nmap", "httpx", "nuclei", "katana"]
    total_steps = len(tools)
    
    progress = ProgressTracker(total_steps)
    progress.start()
    
    for i, tool in enumerate(tools, 1):
        # Simulate tool execution
        format_tool_execution(f"step_{i}", tool, f"{tool} -target example.com")
        time.sleep(1.5)
        
        # Update progress with tool name
        progress.update(i, tool)
        
        # Simulate output save
        output_path = f"/tmp/reconflow/test/{tool}_output.txt"
        format_output_saved(output_path)
        time.sleep(0.5)
    
    progress.complete()

def test_error_messages():
    """Test professional error message formatting."""
    print("\n" + "=" * 60)
    console.print("[bold cyan]Testing Error Message Formatting[/bold cyan]")
    print("=" * 60)
    print()
    
    # Test command not found error
    format_error(
        title="Command Not Found",
        reason="Tool 'qsreplace' is not installed or not in PATH",
        suggestion="Install qsreplace:\n   go install github.com/tomnomnom/qsreplace@latest"
    )
    
    time.sleep(1)
    
    # Test timeout error
    format_error(
        title="Execution Timeout",
        reason="Command execution exceeded 30 minute timeout limit",
        suggestion="Increase timeout in module definition:\n   timeout: \"1h\""
    )
    
    time.sleep(1)

def test_other_messages():
    """Test other message types."""
    print("\n" + "=" * 60)
    console.print("[bold cyan]Testing Other Message Types[/bold cyan]")
    print("=" * 60)
    print()
    
    format_success("Module execution completed successfully!")
    time.sleep(0.5)
    
    format_warning("This is a warning message")
    time.sleep(0.5)
    
    console.print("\n[bold green]✓[/bold green] All message types tested")

if __name__ == "__main__":
    try:
        # Test 1: Progress with tool names
        test_progress_with_tools()
        
        # Test 2: Error messages
        test_error_messages()
        
        # Test 3: Other messages
        test_other_messages()
        
        print("\n" + "=" * 60)
        format_success("All Tests Completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        console.print(f"\n[red]Test failed: {e}[/red]")
        import traceback
        traceback.print_exc()
