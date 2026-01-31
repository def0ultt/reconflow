"""
Simple standalone test for progress tracker.
Tests the progress indicator without full module execution.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.progress import ProgressTracker

def simulate_module_execution(total_steps=5):
    """
    Simulate a module execution with multiple steps.
    """
    print("Starting simulated module execution...")
    print(f"Total steps: {total_steps}\n")
    
    # Create and start progress tracker
    progress = ProgressTracker(total_steps)
    progress.start()
    
    # Simulate step execution
    for step in range(1, total_steps + 1):
        # Simulate work being done
        time.sleep(1.5)  # Each step takes 1.5 seconds
        
        # Update progress
        progress.update(step)
    
    # Mark as complete
    progress.complete()
    
    print("Simulation finished!\n")

if __name__ == "__main__":
    print("=" * 60)
    print("Progress Tracker Test")
    print("=" * 60)
    print()
    
    # Test with 5 steps
    simulate_module_execution(total_steps=5)
    
    print("\nTest completed successfully!")
