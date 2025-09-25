#!/usr/bin/env python3
"""
Tool Registry
Tool registry - Manage all available tools
"""

from typing import Dict, List, Any, Callable
from dataclasses import dataclass


@dataclass
class ToolFunction:
    """Tool function data class"""
    name: str
    function: Callable
    schema: Dict[str, Any]
    description: str = ""


class ToolRegistry:
    """Tool registry"""
    
    def __init__(self):
        self._tools: Dict[str, ToolFunction] = {}
    
    def register(self, name: str, function: Callable, schema: Dict[str, Any], description: str = ""):
        """Register tool
        
        Args:
            name: Tool name
            function: Tool function
            schema: OpenAI format tool schema
            description: Tool description
        """
        self._tools[name] = ToolFunction(
            name=name,
            function=function,
            schema=schema,
            description=description
        )
    
    def get_tool(self, name: str) -> ToolFunction:
        """Get tool"""
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[ToolFunction]:
        """Get all tools"""
        return list(self._tools.values())
    
    def get_tool_names(self) -> List[str]:
        """Get all tool names"""
        return list(self._tools.keys())


# Global tool registry instance
registry = ToolRegistry()