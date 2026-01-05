#!/usr/bin/env python3
"""
Real World Tools Package
Package containing all real-world tools
"""

import os
import importlib
from typing import Dict, List, Any, Callable
from pathlib import Path


def get_all_tools() -> List[Dict[str, Any]]:
    """
    Get schema list of all available tools
    
    Returns:
        List[Dict]: Tool schema list
    """
    # Ensure all tools are registered
    _ensure_all_tools_registered()
    
    # Get schemas of all tools from tool registry
    from ..tool_registry import registry
    tools = []
    
    for tool_func in registry.get_all_tools():
        tools.append(tool_func.schema)
    
    return tools


def execute_tool(tool_name: str, parameters: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
    """
    Execute specified tool
    
    Args:
        tool_name: Tool name
        parameters: Tool parameter dictionary (optional)
        **kwargs: Keyword arguments (compatible with evaluation system call method)
        
    Returns:
        Dict: Tool execution result
    """
    # First ensure all tools are registered
    _ensure_all_tools_registered()
    
    # Handle parameters: prioritize parameters, use kwargs if none
    if parameters is None:
        parameters = kwargs
    
    # Get tool from tool registry
    from ..tool_registry import registry
    tool_func_obj = registry.get_tool(tool_name)
    
    if tool_func_obj:
        try:
            # Execute tool function
            return tool_func_obj.function(**parameters)
        except Exception as e:
            return {
                "error": f"Error executing tool '{tool_name}': {str(e)}",
                "tool_name": tool_name,
                "parameters": parameters
            }
    
    # If tool not found, return error
    return {
        "error": f"Tool '{tool_name}' not found",
        "available_tools": registry.get_tool_names()
    }


def _ensure_all_tools_registered():
    """Ensure all tools are registered"""
    current_dir = Path(__file__).parent
    
    # Iterate through all Python files and import them, trigger tool registration
    success_count = 0
    error_count = 0
    
    for py_file in current_dir.glob("*.py"):
        if py_file.name in ["__init__.py"]:
            continue
            
        module_name = py_file.stem
        try:
            # Dynamically import module, this will trigger register_tool() calls in module
            importlib.import_module(f"tools.real_world.{module_name}")
            success_count += 1
        except Exception as e:
            print(f"Warning: Unable to import tool module {module_name}: {e}")
            error_count += 1
            continue


# Export main functions
__all__ = ['get_all_tools', 'execute_tool']