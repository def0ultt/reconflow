"""
Server-side file reader
Can be used by CLI, API, or UI
"""
import os
import json
from typing import Dict, Any, Optional


class FileReader:
    """Server-side file reader for output files"""
    
    def read_output_file(self, filepath: str) -> Dict[str, Any]:
        """
        Read output file and return structured data
        
        Args:
            filepath: Path to the output file (.txt)
            
        Returns:
            {
                'exists': bool,
                'has_json': bool,
                'json_data': List[Dict] or None,
                'raw_text': str,
                'metadata': Dict or None
            }
        """
        # Check if file exists
        if not os.path.exists(filepath):
            return {
                'exists': False,
                'has_json': False,
                'json_data': None,
                'raw_text': '',
                'metadata': None
            }
        
        result = {'exists': True}
        
        # Read raw text
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                result['raw_text'] = f.read()
        except Exception as e:
            result['raw_text'] = f"Error reading file: {e}"
        
        # Try to read JSON file
        json_path = filepath.replace('.txt', '.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    result['json_data'] = json.load(f)
                    result['has_json'] = True
            except Exception as e:
                result['has_json'] = False
                result['json_data'] = None
                print(f"[!] Failed to read JSON file: {e}")
        else:
            result['has_json'] = False
            result['json_data'] = None
        
        # Read metadata
        meta_path = filepath.replace('.txt', '.meta.json')
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    result['metadata'] = json.load(f)
            except Exception as e:
                result['metadata'] = None
                print(f"[!] Failed to read metadata: {e}")
        else:
            result['metadata'] = None
        
        return result
    
    def list_output_files(self, directory: str) -> list:
        """
        List all output files in a directory
        
        Args:
            directory: Directory path
            
        Returns:
            List of file paths
        """
        if not os.path.exists(directory):
            return []
        
        files = []
        for filename in os.listdir(directory):
            if filename.endswith('.txt') and not filename.endswith('.meta.json'):
                filepath = os.path.join(directory, filename)
                files.append(filepath)
        
        return sorted(files)
