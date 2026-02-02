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

    def print_entry(self, entry: Dict[str, Any]):
        """
        Print entry in a readable key-value format.
        """
        if not isinstance(entry, dict):
            # Skip non-dict entries as requested
            return

        # Define priority fields order for consistent display
        priority = [
            'url', 'host', 'host_ip', 'port', 'scheme', 
            'status_code', 'title', 'content_length', 'time', 'tech'
        ]
        
        # Print keys in priority order first
        for key in priority:
            if key in entry:
                val = entry[key]
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)
                print(f"  {key}: {val}")
        
        # Print remaining keys
        for key, val in entry.items():
            if key not in priority:
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)
                print(f"  {key}: {val}")
        
        print() # Newline between entries
