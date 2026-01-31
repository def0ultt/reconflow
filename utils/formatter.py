"""
Server-side formatting utilities
Generates formatted output data structures (not rendering)
"""
from typing import List, Dict, Any
import json


class OutputFormatter:
    """Server-side output formatter for JSON data"""
    
    def format_as_table_data(self, json_data: List[Dict]) -> Dict[str, Any]:
        """
        Format JSON data for table display
        Returns table structure (not rendered table)
        
        Args:
            json_data: List of JSON records
            
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
        
        # Auto-detect columns from first record
        first_record = json_data[0]
        if not isinstance(first_record, dict):
            # Fallback: convert to dict
            columns = ['value']
            rows = [[str(record)] for record in json_data]
        else:
            columns = list(first_record.keys())
            
            # Build rows
            rows = []
            for record in json_data:
                row = [str(record.get(col, '')) for col in columns]
                rows.append(row)
        
        return {
            'columns': columns,
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
