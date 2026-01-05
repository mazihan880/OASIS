#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database_store tool implementation
database_store tool
"""

import json
import random
from typing import Dict, Any

# Import task context manager
try:
    # Try relative import first
    from ...evaluation.task_context import task_context
except ImportError:
    try:
        # Try absolute import as fallback
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))  
        from evaluation.task_context import task_context
    except ImportError:
        # Create a dummy task context if import fails
        class DummytasksContext:
            def get_current_task_id(self):
                return None
            def get_task_data(self, task_id):
                return None
            def is_task_active(self):
                return False
        task_context = DummytasksContext()

def database_store(*args, **kwargs) -> Dict[str, Any]:
    """
    database_store tool
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Dict containing the operation response
    """
    
    try:
        # Generate response (no specific task data for database_store)
        current_task_id = task_context.get_current_task_id() if task_context.is_task_active() else None
        
        # Generate fallback response
        response = {
            "status": "success",
            "message": "Data stored successfully",
            "tool": "database_store",
                "method": "fallback",
                "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                "current_task_id": current_task_id
            }
        }
        
        # Add tool-specific fields
        response.update({"record_id": f"rec_{random.randint(1000, 9999)}"})
        
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to execute database_store: {str(e)}",
            "tool": "database_store"
        }

# Tool registration schema
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "database_store",
        "description": "database_store tool",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "Data to store in database"
                }
            },
            "required": ["data"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="database_store",
        function=database_store,
        schema=TOOL_SCHEMA,
        description="Tool function for database_store"
    )

# Auto-register when module is imported
register_tool()
