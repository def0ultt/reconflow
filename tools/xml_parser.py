#!/usr/bin/env python3
import argparse
import sys
import xml.etree.ElementTree as ET
from rich.console import Console
from rich.table import Table
from rich import box

def xml_to_dict(element):
    """
    Recursively convert XML element to dictionary.
    """
    node = {}
    
    # Attributes
    if element.attrib:
        node.update(element.attrib)
    
    # Text content
    text = element.text
    if text and text.strip():
        node['text'] = text.strip()
    
    # Children
    for child in element:
        child_data = xml_to_dict(child)
        tag = child.tag
        
        if tag in node:
            if isinstance(node[tag], list):
                node[tag].append(child_data)
            else:
                node[tag] = [node[tag], child_data]
        else:
            node[tag] = child_data
            
    return node

def display_dict(data, console, title="XML Data"):
    # If list of uniform dicts, show list table
    # If single dict, show key-value table
    
    if isinstance(data, dict):
        # Flatten simple dicts for better display?
        table = Table(title=title, box=box.ROUNDED, show_header=True)
        table.add_column("Tag/Attr", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        
        for k, v in data.items():
            val_str = str(v)
            if isinstance(v, (dict, list)):
                # Just show type or summary for complex nested structures to avoid huge output
                # Or JSON dump it
                import json
                try:
                    val_str = json.dumps(v, indent=2) 
                except:
                    pass
            table.add_row(str(k), val_str)
            
        console.print(table)
        
    elif isinstance(data, list):
         # Try to make a table if items look similar
        if not data:
            console.print("[yellow]Empty list.[/yellow]")
            return
            
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        table = Table(title=title, box=box.ROUNDED)
        sorted_keys = sorted(list(all_keys))
        for key in sorted_keys:
            table.add_column(key, style="cyan")
            
        for item in data:
            if not isinstance(item, dict): continue
            row = []
            for key in sorted_keys:
                val = item.get(key, "")
                if isinstance(val, (dict, list)):
                     val = "..." # Compress nested in list view
                row.append(str(val))
            table.add_row(*row)
            
        console.print(table)
    else:
        console.print(str(data))


def main():
    parser = argparse.ArgumentParser(description="Generic XML Visualizer")
    parser.add_argument("-i", "--input", required=True, help="Input formatted XML file")
    args = parser.parse_args()

    console = Console()

    try:
        tree = ET.parse(args.input)
        root = tree.getroot()
        data = {root.tag: xml_to_dict(root)}
        
    except FileNotFoundError:
        console.print(f"[red]Error: Input file '{args.input}' not found.[/red]")
        sys.exit(1)
    except ET.ParseError as e:
        console.print(f"[red]Error: Failed to parse XML: {e}[/red]")
        sys.exit(1)

    # Simplified display: Unwrap root if it usually contains the list
    # e.g. <scan><host>...</host><host>...</host></scan> -> display usage of 'host' list
    
    # Check if root has single child which is a list?
    # For now, just display the full dict conversion
    display_dict(data, console, title=f"XML: {args.input}")

if __name__ == "__main__":
    main()
