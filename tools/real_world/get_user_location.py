#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get User Location Tool - tasks-Aware Version
Attempt to determine user location from public check-ins or posts
"""

import json
import random
import re
from typing import Dict, Any, Optional
from difflib import SequenceMatcher

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

# Import resource data
try:
    from ..resource.get_user_location_data import TASK_DATA, DEFAULT_LOCATION_RESULT
except ImportError:
    TASK_DATA = {}
    DEFAULT_LOCATION_RESULT = {"status": "error", "message": "Resource data not available"}

def get_user_location(*args, **kwargs) -> Dict[str, Any]:
    """
    Attempt to determine user location from public check-ins or posts with task context support
    
    Args:
        *args: Positional arguments (username, query, etc.)
        **kwargs: Keyword arguments (username, query, user_id, etc.)
    
    Returns:
        Dict containing the location search response
    """
    
    try:
        # Extract location parameters
        target = None
        
        # Handle positional arguments
        if len(args) >= 1:
            target = str(args[0])
        
        # Handle keyword arguments
        if 'target' in kwargs:
            target = str(kwargs['target'])
        
        # Check for task context first (priority)
        if task_context.is_task_active():
            current_task_id = task_context.get_current_task_id()
            if current_task_id and current_task_id in TASK_DATA:
                task_data = TASK_DATA[current_task_id]
                
                # For multi-call tasks, find the best matching call within the task
                if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                    # Build query string for matching
                    def build_query_string(target):
                        return f"{target or ''}".strip().lower()
                    
                    query_string = build_query_string(target)
                    best_call_index = None
                    best_score = -1
                    
                    # Find best matching call using query similarity
                    for i, call_data in enumerate(task_data['calls']):
                        call_queries = call_data.get('queries', [])
                        for query in call_queries:
                            score = SequenceMatcher(None, query_string, query.lower()).ratio()
                            if score > best_score:
                                best_score = score
                                best_call_index = i
                    
                    # If no match found, fallback to first call
                    if best_call_index is None:
                        best_call_index = 0
                        best_score = 0.0
                    
                    call_data = task_data['calls'][best_call_index]
                    result = call_data.get('result', DEFAULT_LOCATION_RESULT).copy()
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': best_call_index,
                        'task_active': True,
                        'target_used': target,
                        'best_score': best_score,
                        'task_id': current_task_id,
                        'scenario': task_data.get('scenario', 'unknown'),
                        'matched_task': True,
                        'multi_call': True
                    }
                else:
                    # Single call task - use task-level result directly
                    result = task_data.get('result', DEFAULT_LOCATION_RESULT).copy()
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': None,
                        'task_active': True,
                        'target_used': target,
                        'task_id': current_task_id,
                        'scenario': task_data.get('scenario', 'unknown'),
                        'matched_task': True,
                        'multi_call': False
                    }
        
        # Fallback to intelligent matching
        # Use target as search query
        search_query = target if target else "user location"
        
        # Find best matching task
        best_match = find_best_matching_task(search_query, target)
        
        if best_match:
            task_id, similarity_score = best_match
            result = TASK_DATA[task_id]["result"].copy()
            
            # Add matching information to result (for debugging)
                "method": "similarity_match",
                "matched_task_id": task_id,
                "similarity_score": similarity_score,
                "original_query": search_query,
                "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                "matched_task": True,
                "multi_call": False
            }
            
        
        # No match found, return fallback response
        result = generate_fallback_response(target)
            'method': 'default_fallback',
            'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            'matched_task': False,
            'multi_call': False,
            'matched_task_id': None
        }
        
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Failed to execute get_user_location: {str(e)}",
            "tool": "get_user_location"
        }
            "method": "exception_fallback",
            "error": str(e),
            "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            "matched_task": False,
            "multi_call": False,
            "matched_task_id": None
        }

def find_best_matching_task(query: str, target: str = None) -> Optional[tuple]:
    """
    Find the best matching task based on query similarity
    
    Args:
        query: Search query
        target: Target username or search term
    
    Returns:
        Tuple of (task_id, similarity_score) or None if no good match
    """
    
    if not TASK_DATA:
        return None
    
    normalized_query = normalize_query(query)
    best_match = None
    best_score = 0.0
    
    for task_id, task_data in TASK_DATA.items():
        queries = task_data.get("queries", [])
        
        for task_query in queries:
            normalized_task_query = normalize_query(task_query)
            
            # Calculate base similarity score
            similarity = SequenceMatcher(None, normalized_query, normalized_task_query).ratio()
            
            # Only boost for exact matches
            if target and target == task_query:
                similarity = 2.0  # Perfect match
            elif target and target.lower() == task_query.lower():
                similarity = 1.8  # Case-insensitive exact match
            elif target and target in task_query:
                similarity += 0.3  # Partial match
            
            if similarity > best_score:
                best_score = similarity
                best_match = (task_id, similarity)
    
    # Return match only if similarity is above threshold
    if best_score >= 0.5:
        return best_match
    
    return None

def normalize_query(query: str) -> str:
    """
    Normalize query for better matching
    """
    if not query:
        return ""
    
    # Convert to lowercase and remove extra whitespace
    normalized = re.sub(r'\s+', ' ', query.lower().strip())
    
    # Remove common punctuation
    normalized = re.sub(r'[.,!?;:"\'@]', '', normalized)
    
    return normalized

def generate_fallback_response(target: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific match is found
    """
    
    response = DEFAULT_LOCATION_RESULT.copy()
    
    # Customize message based on target
    if target:
        response["message"] = f"Location search completed for {target}"
        response["location"] = f"Location found for {target}"
    else:
        response["message"] = "Location search completed"
        response["location"] = "Location found"
    
    # Add random coordinates for fallback
    response["latitude"] = round(random.uniform(34.0, 40.0), 4)
    response["longitude"] = round(random.uniform(-122.0, -118.0), 4)
    response["accuracy"] = f"{random.randint(10, 100)} meters"
    
    # Add random search ID
    response["search_id"] = f"LOC_{random.randint(100000, 999999)}"
    
    return response

# Tool registration schema
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_user_location",
        "description": "After receiving user information, this tool will try to crawl the user's location from the user's social media information (including check-ins, IP location, etc.).",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Username, handle, or search query for location tracking"
                }
            },
            "required": []
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="get_user_location",
        function=get_user_location,
        schema=TOOL_SCHEMA,
        description="Tool function for get_user_location"
    )

# Auto-register when module is imported
register_tool()
