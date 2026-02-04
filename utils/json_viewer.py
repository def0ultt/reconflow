"""
Generic JSON Log Viewer
Replaces old rich-based table view with a flexible text-based viewer using
advanced searching similar to JQ but simpler.
"""
import sys
import json
import re
from typing import List, Dict, Any, Optional
from collections import Counter


class JsonLogViewer:
    def __init__(self, data: List[Dict]):
        """
        Initialize with already parsed list of dicts.
        """
        self.data = data

    @staticmethod
    def _match_value(actual: Any, operator: str, expected_str: str) -> bool:
        """
        Helper for single condition matching.
        Operators: ==, !=, >, <, >=, <=, ~= (contains/regex-ish)
        For strings, wildcards * are supported in == and !=.
        """
        if actual is None:
            return False
            
        # Convert actual to appropriate type for comparison if possible
        actual_str = str(actual)
        
        # Handle Wildcards for Strings
        if operator in ('==', '!='):
            if '*' in expected_str:
                # Convert glob * to regex .*
                # Escape other chars
                pattern = re.escape(expected_str).replace(r'\*', '.*')
                match = re.fullmatch(pattern, actual_str, re.IGNORECASE)
                
                if operator == '==':
                    return bool(match)
                else:
                    return not bool(match)

        # Standard Comparisons
        try:
            # Try numeric comparison first
            if operator in ('>', '<', '>=', '<='):
                val_num = float(actual)
                exp_num = float(expected_str)
                if operator == '>': return val_num > exp_num
                if operator == '<': return val_num < exp_num
                if operator == '>=': return val_num >= exp_num
                if operator == '<=': return val_num <= exp_num
            
            # Equality checks
            if operator == '==':
                # Try int/float
                try:
                    return float(actual) == float(expected_str)
                except:
                    return actual_str.lower() == expected_str.lower()
            
            if operator == '!=':
                try:
                    return float(actual) != float(expected_str)
                except:
                    return actual_str.lower() != expected_str.lower()
                    
            if operator == '~=':
                # Contains (case-insensitive)
                if isinstance(actual, list):
                     return any(expected_str.lower() in str(i).lower() for i in actual)
                return expected_str.lower() in actual_str.lower()
                
        except Exception:
            # Fallback to string comparison or False on error
            pass
            
        return False

    def advanced_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Advanced search with logical operators (&&, ||) and comparisons.
        Example: 'status_code==200 && url==*admin*'
        """
        if not query or not query.strip():
            return self.data

        logging_results = []
        
        # We need to parse the query into conditions.
        # This is a simple parser that supports && and ||.
        # Precedence: AND before OR (standard).
        # We'll split by || first, then by &&.
        
        or_groups = query.split('||')
        
        filtered_results = []
        
        for record in self.data:
            # Handle non-dict records
            if not isinstance(record, dict):
                 # For now, we skip non-dict records in advanced search 
                 # or we could try to match against the raw value if field is 'value' or something
                 continue
                 
            record_match = False
            
            # Interpret OR groups (if any of these match, the record matches)
            for group in or_groups:
                # Within an OR group, all AND conditions must match
                and_conditions = group.split('&&')
                group_match = True
                
                for condition in and_conditions:
                    condition = condition.strip()
                    if not condition: continue
                    
                    # Parse operator
                    # Sort by length desc to match >=, <= matched before > or <
                    ops = ['==', '!=', '>=', '<=', '>', '<', '~=']
                    operator = None
                    field = None
                    value = None
                    
                    for op in ops:
                        if op in condition:
                            operator = op
                            parts = condition.split(op, 1) # Split only on first occurrence
                            field = parts[0].strip()
                            value = parts[1].strip().strip('"').strip("'")
                            break
                    
                    if not operator:
                        # Invalid condition syntax, treat as Fail
                        group_match = False
                        break
                    
                    # Check match
                    val = record.get(field)
                    if not self._match_value(val, operator, value):
                        group_match = False
                        break
                
                if group_match:
                    record_match = True
                    break # Found a matching OR group, no need to check others
            
            if record_match:
                filtered_results.append(record)
                
        return filtered_results

    def _classify_value_type(self, value: str) -> str:
        """
        Classify value type for intelligent colorization.
        
        Returns: 'url', 'number', 'content_type', 'tech', or 'default'
        """
        value_str = str(value)
        
        # URL
        if '://' in value_str or value_str.startswith(('http://', 'https://')):
            return 'url'
        
        # Number
        if re.fullmatch(r'\d+(\.\d+)?', value_str):
            return 'number'
        
        # Content type
        if any(x in value_str for x in ['text/', 'application/', 'image/', 'video/', 'audio/']):
            return 'content_type'
        
        # Technology/Version (e.g., nginx:1.18, FrontPage:6.0)
        if re.search(r'[a-zA-Z]+[:/]\d', value_str):
            return 'tech'
        
        return 'default'
    
    def _colorize_value(self, value: str, value_type: str) -> str:
        """Apply color markup based on value type."""
        colors = {
            'url': 'cyan',
            'number': 'yellow',
            'content_type': 'magenta',
            'tech': 'green',
            'default': 'white'
        }
        color = colors.get(value_type, 'white')
        return f"[{color}]{value}[/{color}]"
    
    def print_entry(self, entry: Dict[str, Any], 
                    include_fields: List[str] = None,
                    exclude_fields: List[str] = None):
        """
        Print entry in a readable key-value format.
        
        Args:
            entry: Dictionary to print
            include_fields: If provided, only print these fields
            exclude_fields: If provided, print all fields except these
        """
        if not isinstance(entry, dict):
            # Skip non-dict entries as requested
            return

        # Define priority fields order for consistent display
        priority = [
            'url', 'host', 'host_ip', 'port', 'scheme', 
            'status_code', 'title', 'content_length', 'time', 'tech'
        ]
        
        # Determine which fields to print
        if include_fields:
            # Only print specified fields, maintain priority order
            fields_to_print = []
            # Add priority fields that are in include list
            for field in priority:
                if field in include_fields and field in entry:
                    fields_to_print.append(field)
            # Add remaining include fields not in priority
            for field in include_fields:
                if field not in priority and field in entry:
                    fields_to_print.append(field)
        elif exclude_fields:
            # Print all fields except excluded ones
            fields_to_print = []
            # Add priority fields not in exclude list
            for field in priority:
                if field not in exclude_fields and field in entry:
                    fields_to_print.append(field)
            # Add remaining fields not in priority or exclude
            for field in entry.keys():
                if field not in priority and field not in exclude_fields:
                    fields_to_print.append(field)
        else:
            # Print all fields in priority order
            fields_to_print = []
            for field in priority:
                if field in entry:
                    fields_to_print.append(field)
            for field in entry.keys():
                if field not in priority:
                    fields_to_print.append(field)
        
        # Print the fields with colorization
        from rich.console import Console
        console = Console()
        
        for key in fields_to_print:
            val = entry[key]
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            
            # Classify and colorize the value
            val_str = str(val)
            val_type = self._classify_value_type(val_str)
            colored_val = self._colorize_value(val_str, val_type)
            
            # Print with colored key (blue) and colored value
            console.print(f"  [bold blue]{key}[/bold blue]: {colored_val}")
        
        console.print() # Newline between entries
