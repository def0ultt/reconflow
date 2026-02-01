"""
Progress tracking and display utilities for ReconFlow module execution.
Provides animated progress bars, step counters, and completion notifications.
"""

import sys
import threading
import time
from typing import Optional
from rich.console import Console

console = Console()


class ProgressTracker:
    """
    Thread-safe progress tracker with animated display.
    
    Features:
    - Step counter (e.g., "Step 3/10")
    - Visual progress bar using Unicode blocks
    - Animated spinner
    - Tool name display
    - Colored output
    - Clean terminal updates
    """
    
    # Animation frames for spinner
    SPINNER_FRAMES = ["[→   ]", "[ →  ]", "[  → ]", "[   →]"]
    
    # Progress bar characters
    FILLED_BLOCK = "▓"
    EMPTY_BLOCK = "░"
    BAR_LENGTH = 10
    
    def __init__(self, total_steps: int):
        """
        Initialize progress tracker.
        
        Args:
            total_steps: Total number of steps to track
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.current_tool = ""
        self.completed = False
        self._lock = threading.Lock()
        self._animation_thread: Optional[threading.Thread] = None
        self._stop_animation = threading.Event()
        self._frame_index = 0
        
    def start(self):
        """Start the progress display with animation."""
        self._stop_animation.clear()
        self._animation_thread = threading.Thread(target=self._animate, daemon=True)
        self._animation_thread.start()
        
    def update(self, step_number: int, tool_name: str = ""):
        """
        Update progress to a specific step.
        
        Args:
            step_number: Current step number (1-indexed)
            tool_name: Name of the tool being executed
        """
        with self._lock:
            self.current_step = step_number
            if tool_name:
                self.current_tool = tool_name
            
    def set_current_tool(self, tool_name: str):
        """
        Set the currently running tool name.
        
        Args:
            tool_name: Name of the tool
        """
        with self._lock:
            self.current_tool = tool_name
            
    def increment(self, tool_name: str = ""):
        """
        Increment progress by one step.
        
        Args:
            tool_name: Name of the tool being executed
        """
        with self._lock:
            self.current_step += 1
            if tool_name:
                self.current_tool = tool_name
            
    def complete(self):
        """Mark progress as complete and show completion message."""
        with self._lock:
            self.completed = True
            self.current_step = self.total_steps
            
        # Stop animation
        self._stop_animation.set()
        if self._animation_thread:
            self._animation_thread.join(timeout=1.0)
            
        # Clear current line and show completion
        self._clear_line()
        console.print("\n✅ [bold green]Execution Completed Successfully![/bold green]\n")
        
    def _animate(self):
        """Animation loop that updates the display."""
        while not self._stop_animation.is_set():
            with self._lock:
                if self.completed:
                    break
                    
                # Get current state
                current = self.current_step
                total = self.total_steps
                tool = self.current_tool
                
                # Calculate progress percentage
                if total > 0:
                    progress = current / total
                else:
                    progress = 0
                    
                # Build progress bar
                filled_blocks = int(progress * self.BAR_LENGTH)
                empty_blocks = self.BAR_LENGTH - filled_blocks
                bar = f"{self.FILLED_BLOCK * filled_blocks}{self.EMPTY_BLOCK * empty_blocks}"
                
                # Get spinner frame
                spinner = self.SPINNER_FRAMES[self._frame_index % len(self.SPINNER_FRAMES)]
                
                # Build display line with colors
                # Format: [→   ] Step X/Y  ▓▓░░░░░░░░  Running TOOL...
                display_parts = [
                    f"[cyan]{spinner}[/cyan]",
                    f"[bold cyan]Step {current}/{total}[/bold cyan]",
                    f" [green]{self.FILLED_BLOCK * filled_blocks}[/green][dim white]{self.EMPTY_BLOCK * empty_blocks}[/dim white] "
                ]
                
                if tool:
                    display_parts.append(f"[yellow]Running {tool}...[/yellow]")
                else:
                    display_parts.append("[dim]Processing...[/dim]")
                
                display_text = " ".join(display_parts)
                
            # Clear line and write new content
            sys.stdout.write('\r' + ' ' * 120 + '\r')
            console.print(display_text, end='')
            
            # Update frame index
            self._frame_index += 1
            
            # Wait before next update
            time.sleep(0.3)
            
    def _clear_line(self):
        """Clear the current terminal line."""
        sys.stdout.write('\r' + ' ' * 120 + '\r')
        sys.stdout.flush()
        
    def stop(self):
        """Stop the progress tracker (cleanup)."""
        self._stop_animation.set()
        if self._animation_thread:
            self._animation_thread.join(timeout=1.0)
        self._clear_line()
