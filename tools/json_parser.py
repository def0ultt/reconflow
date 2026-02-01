#!/usr/bin/env python3
import argparse
import json
import sys
from rich.console import Console
from rich.table import Table
from rich import box

def main():
    parser = argparse.ArgumentParser(description="Generic JSON Visualizer")
    parser.add_argument("-i", "--input", required=True, help="Input formatted JSON file")
    args = parser.parse_args()

    console = Console()

    try:
        with open(args.input, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        console.print(f"[red]Error: Input file '{args.input}' not found.[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Failed to parse JSON: {e}[/red]")
        sys.exit(1)

    if not data:
        console.print("[yellow]Empty data.[/yellow]")
        return

    # Normalize data to a list of dicts
    if isinstance(data, dict):
        # Case 1: Single Dict -> Table with Key | Value
        table = Table(title=f"Data from {args.input}", box=box.ROUNDED, show_header=True)
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        
        for k, v in data.items():
            val_str = str(v)
            if isinstance(v, (dict, list)):
                val_str = json.dumps(v, indent=2)
            table.add_row(str(k), val_str)
            
        console.print(table)
        return

    elif isinstance(data, list):
        if not data:
            console.print("[yellow]Empty list.[/yellow]")
            return
            
        # Case 2: List of Dicts -> Table where keys are columns
        # First, gather all unique keys to define columns
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
            else:
                # List of primitives?
                table = Table(title=f"List from {args.input}", box=box.ROUNDED)
                table.add_column("Value", style="cyan")
                for val in data:
                    table.add_row(str(val))
                console.print(table)
                return

        # Sort keys for consistent order
        sorted_keys = sorted(list(all_keys))
        
        table = Table(title=f"Results from {args.input}", box=box.ROUNDED)
        for key in sorted_keys:
            table.add_column(key.capitalize(), style="cyan", overflow="fold")

        for item in data:
            if not isinstance(item, dict): continue
            row_data = []
            for key in sorted_keys:
                val = item.get(key, "")
                if isinstance(val, (dict, list)):
                    val = json.dumps(val)
                row_data.append(str(val))
            table.add_row(*row_data)

        console.print(table)

    else:
        console.print(f"[bold]{str(data)}[/bold]")

if __name__ == "__main__":
    main()
