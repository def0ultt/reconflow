"""
Server-side formatting utilities
Generates formatted output data structures (not rendering)
"""
from typing import List, Dict, Any
import json


class OutputFormatter:
    """Server-side output formatter for JSON data"""
    
    def format_as_table_data(self, json_data: List[Dict], columns: List[str] = None) -> Dict[str, Any]:
        """
        Format JSON data for table display
        Returns table structure (not rendered table)
        
        Args:
            json_data: List of JSON records
            columns: Optional list of columns to display. If None, auto-detects from first record.
            
        Returns:
            {
                'columns': ['col1', 'col2', ...],
                'rows': [['val1', 'val2'], ...],
                'total': 10
            }
        """
        if not json_data or not isinstance(json_data, list):
            return {
                'columns': [],
                'rows': [],
                'total': 0
            }
        
        # Handle empty list
        if len(json_data) == 0:
            return {
                'columns': [],
                'rows': [],
                'total': 0
            }
        
        # Determine columns
        if columns:
            target_columns = columns
        else:
            # Auto-detect columns from first record
            first_record = json_data[0]
            if not isinstance(first_record, dict):
                # Fallback: convert to dict
                target_columns = ['value']
                json_data = [{'value': str(record)} for record in json_data]
            else:
                target_columns = list(first_record.keys())
            
        # Build rows
        rows = []
        for record in json_data:
            # Handle non-dict records if columns provided manually
            if not isinstance(record, dict) and columns:
                 # This is tricky, but assuming record is dict if columns are requested
                 record = {} 
            
            row = []
            for col in target_columns:
                val = record.get(col, '')
                # Handle lists/dicts in cells
                if isinstance(val, list):
                    # Convert list to comma-separated string
                    # Filter out non-string items if needed, but simple str() usually works
                    val = ", ".join(str(item) for item in val)
                elif isinstance(val, dict):
                     val = json.dumps(val)
                
                row.append(str(val))
            rows.append(row)
        
        return {
            'columns': target_columns,
            'rows': rows,
            'total': len(json_data)
        }
    
    def format_as_json_string(self, data: Any, indent: int = 2) -> str:
        """
        Format data as pretty JSON string
        
        Args:
            data: Any JSON-serializable data
            indent: Indentation level
            
        Returns:
            Pretty-printed JSON string
        """
        return json.dumps(data, indent=indent, ensure_ascii=False)
    
    def truncate_text(self, text: str, max_length: int = 100) -> str:
        """
        Truncate text to max length
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text with ellipsis if needed
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'
