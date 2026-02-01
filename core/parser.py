"""
Server-side output parser system
Can be used by CLI, API, or UI
"""
from typing import List, Dict, Optional, Callable
import json


class OutputParser:
    """Server-side output parser for tool outputs"""
    
    def __init__(self):
        self.builtin_parsers: Dict[str, Callable] = {}
    
    def parse_to_json(self, stdout: str, tool_name: str) -> Optional[List[Dict]]:
        """
        Parse tool output to JSON
        
        Args:
            stdout: Tool output string
            tool_name: Name of the tool that generated output
            
        Returns:
            List of JSON records or None if parsing fails
        """
        if not stdout or not stdout.strip():
            return None
        
        # 1. Try direct JSON parsing (tool outputs JSON)
        try:
            data = json.loads(stdout)
            # Ensure it's a list
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                return [{'value': data}]
        except (json.JSONDecodeError, ValueError):
            pass
        
        # 2. Try JSON lines format (one JSON per line)
        try:
            results = []
            for line in stdout.splitlines():
                line = line.strip()
                if line:
                    try:
                        results.append(json.loads(line))
                    except:
                        pass
            if results:
                return results
        except:
            pass
        
        # 3. Use built-in parser if available
        if tool_name in self.builtin_parsers:
            try:
                parser = self.builtin_parsers[tool_name]
                result = parser(stdout)
                if result:
                    return result
            except Exception as e:
                print(f"[!] Built-in parser for '{tool_name}' failed: {e}")
        
        # 4. Fallback: line-based JSON (one record per line)
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        if lines:
            return [{'line': line} for line in lines]
        
        return None
    
    def register_parser(self, tool_name: str, parser_func: Callable):
        """
        Register a custom parser for a tool
        
        Args:
            tool_name: Name of the tool
            parser_func: Function that takes stdout and returns List[Dict]
        """
        self.builtin_parsers[tool_name] = parser_func
    
    def has_parser(self, tool_name: str) -> bool:
        """Check if a parser is registered for a tool"""
        return tool_name in self.builtin_parsers
