#!/usr/bin/env python3
"""
analyze_image_content tool implementation - tasks-Aware Version
Analyzes and describes image content with task context support
"""

import json
from typing import Dict, Any, List
from difflib import SequenceMatcher
import os

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

# Import the data
try:
    from tools.resource.analyze_image_content_data import TASK_DATA, DEFAULT_ANALYSIS_RESULT
except ImportError:
    TASK_DATA = {}
    DEFAULT_ANALYSIS_RESULT = {
        "status": "success",
        "message": "Image analysis completed",
        "description": "Image content analyzed successfully",
        "confidence_score": 0.95
    }

def find_best_matching_task(image_path: str, call_index: int = None) -> Dict[str, Any]:
    """
    Find the best matching task for the given image path
    Supports both single tasks and multi-call tasks with calls array.
    
    Args:
        image_path: The image path to search for
        call_index: Index for multi-call tasks
        
    Returns:
        Dictionary containing the matched task data and similarity score
    """
    if not TASK_DATA:
        return {
            'matched_task_id': None,
            'similarity_score': 0.0,
            'result': DEFAULT_ANALYSIS_RESULT,
            'call_index': None
        }
    
    best_match = None
    best_score = 0.0
    best_task_id = None
    best_call_index = None
    
    image_path_lower = image_path.lower().strip()
    
    for task_id, task_data in TASK_DATA.items():
        # Handle new calls array structure for multi-call tasks
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            for call_idx, call_data in enumerate(task_data['calls']):
                queries = call_data.get('queries', [])
                
                for query in queries:
                    query_lower = query.lower().strip()
                    
                    # Calculate similarity score
                    similarity = SequenceMatcher(None, image_path_lower, query_lower).ratio()
                    
                    # Boost score for exact matches
                    if image_path_lower == query_lower:
                        similarity += 1.0
                    
                    # Boost score for filename matches
                    image_filename = os.path.basename(image_path_lower)
                    query_filename = os.path.basename(query_lower)
                    if image_filename == query_filename:
                        similarity += 0.8
                    
                    # Boost score for extension matches
                    if image_path_lower.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.mp3')):
                        if query_lower.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.mp3')):
                            similarity += 0.3
                    
                    # Boost score for path containment
                    if image_path_lower in query_lower or query_lower in image_path_lower:
                        similarity += 0.5
                    
                    if similarity > best_score:
                        best_score = similarity
                        best_match = call_data['result']
                        best_task_id = task_id
                        best_call_index = call_idx
        else:
            # Handle legacy single task structure
            queries = task_data.get('queries', [])
            
            for query in queries:
                query_lower = query.lower().strip()
                
                # Calculate similarity score
                similarity = SequenceMatcher(None, image_path_lower, query_lower).ratio()
                
                # Boost score for exact matches
                if image_path_lower == query_lower:
                    similarity += 1.0
                
                # Boost score for filename matches
                image_filename = os.path.basename(image_path_lower)
                query_filename = os.path.basename(query_lower)
                if image_filename == query_filename:
                    similarity += 0.8
                
                # Boost score for extension matches
                if image_path_lower.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.mp3')):
                    if query_lower.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.mp3')):
                        similarity += 0.3
                
                # Boost score for path containment
                if image_path_lower in query_lower or query_lower in image_path_lower:
                    similarity += 0.5
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = task_data['result']
                    best_task_id = task_id
    
    # Use threshold for matching
    if best_score < 1.5:  # Require higher similarity for matching
        return {
            'matched_task_id': None,
            'similarity_score': best_score,
            'result': DEFAULT_ANALYSIS_RESULT,
            'call_index': None
        }
    
    return {
        'matched_task_id': best_task_id,
        'similarity_score': best_score,
        'result': best_match,
        'call_index': best_call_index
    }

def analyze_image_content(*args, **kwargs) -> Dict[str, Any]:
    """
    Analyze and describe image content with task context support
    Supports both single tasks and multi-call tasks with calls array.
    
    Args:
        image_path (str): Path to the image file to analyze
        
    Returns:
        Dict containing the analysis result
    """
    # Handle both positional and keyword arguments
    if args:
        image_path = str(args[0])
    elif 'image_path' in kwargs:
        image_path = str(kwargs['image_path'])
    else:
        return {
            "result": {
                "status": "error",
                "message": "Image path parameter is required",
                "description": "",
                "confidence_score": 0.0
            }
        }
    
    # Priority 1: Use task context data if available
    if task_context.is_task_active():
        current_task_id = task_context.get_current_task_id()
        if current_task_id and current_task_id in TASK_DATA:
            task_data = TASK_DATA[current_task_id]
            
            # Handle calls structure for multi-call tasks
            if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                # Find the best matching call by calculating similarity (no threshold)
                best_call = None
                best_score = -1
                
                for call in task_data['calls']:
                    queries = call.get('queries', [])
                    for query in queries:
                        similarity = SequenceMatcher(None, image_path.lower(), query.lower()).ratio()
                        if similarity > best_score:
                            best_score = similarity
                            best_call = call
                
                # Use the best matching call, or first call if no queries found
                if best_call:
                    call_result = best_call['result']
                else:
                    call_result = task_data['calls'][0]['result']
                
                # Build result structure
                if isinstance(call_result, dict):
                    result = call_result.copy()
                else:
                    result = {
                        "status": "success",
                        "message": "Image analysis completed",
                        "description": str(call_result),
                        "confidence_score": 0.95
                    }
                
                return {
                    "result": result,
                        "method": "task_context",
                        "matched_task_id": current_task_id,
                        "task_active": True,
                        "multi_call": True,
                        "query_match_score": best_score
                    }
                }
            else:
                # Handle legacy single task structure
                task_result = task_data["result"]
                
                # Build result structure
                if isinstance(task_result, dict):
                    result = task_result.copy()
                else:
                    result = {
                        "status": "success",
                        "message": "Image analysis completed",
                        "description": str(task_result),
                        "confidence_score": 0.95
                    }
                
                return {
                    "result": result,
                        "method": "task_context",
                        "matched_task_id": current_task_id,
                        "task_active": True,
                        "multi_call": False
                    }
                }
    
    # Priority 2: Fallback to intelligent matching
    match_info = find_best_matching_task(image_path)
    match_result = match_info['result']
    
    # Build result structure
    if isinstance(match_result, dict):
        result = match_result.copy()
    else:
        result = {
            "status": "success",
            "message": "Image analysis completed",
            "description": str(match_result),
            "confidence_score": 0.95
        }
    
    return {
        "result": result,
            'method': 'intelligent_matching' if match_info['matched_task_id'] else 'fallback',
            'matched_task_id': match_info['matched_task_id'],
            'task_active': task_context.is_task_active(),
            'call_index': match_info.get('call_index'),
            'similarity_score': match_info.get('similarity_score', 0)
        }
    }

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "analyze_image_content",
        "description": "Analyze and describe the content of an image file",
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file to analyze (e.g., '/home/user/image.png', '/path/to/screenshot.jpg')"
                }
            },
            "required": ["image_path"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="analyze_image_content",
        function=analyze_image_content,
        schema=TOOL_SCHEMA,
        description="Tool function for analyze_image_content"
    )

if __name__ == "__main__":
    # Test the tool
    test_cases = [
        "/home/user/bug.png",
        "/downloads/project-45B2022.pdf",
        "~/volt_logo.png",
        "/unknown/path/test.jpg"
    ]
    
    for image_path in test_cases:
        result = analyze_image_content(image_path=image_path)
        if '_match_info' in result:

# Auto-register when module is imported
register_tool()
