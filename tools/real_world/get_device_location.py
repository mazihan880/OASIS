#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_device_location tool implementation - tasks-Aware Version
Tool implementation for getting device location information - tasks-aware version
Uses task context to load specific resource data for deterministic results
"""

import json
import random
from typing import Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
from ..resource.get_device_location_data import TASK_DATA, DEFAULT_LOCATION_RESULT

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
        # If unable to import task context, create empty context object
        class DummytasksContext:
            def get_current_task_id(self) -> Optional[str]:
                return None
            def is_task_active(self) -> bool:
                return False
        task_context = DummytasksContext()

def get_device_location(query: str = "", *args, **kwargs) -> Dict[str, Any]:
    """
    get_device_location tool - Get device GPS location information (tasks-Aware Version)
    
    Args:
        query: Location query (optional)
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Dict containing the GPS location response
    """
    
    try:
        # Priority 1: Use task context data if available
        if task_context.is_task_active():
            current_task_id = task_context.get_current_task_id()
            if current_task_id and current_task_id in TASK_DATA:
                task_data = TASK_DATA[current_task_id]
                
                # For multi-call tasks, find the best matching call within the task
                if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                    best_call_index = None
                    best_score = -1
                    
                    # Build query string for matching
                    def build_query_string(call_data):
                        parts = []
                        if call_data.get('query'):
                            parts.append(call_data['query'])
                        return ' '.join(parts).strip()
                    
                    for i, call_data in enumerate(task_data['calls']):
                        call_query = build_query_string(call_data)
                        
                        # Calculate query similarity using SequenceMatcher
                        if query and call_query:
                            score = SequenceMatcher(None, query.lower(), call_query.lower()).ratio()
                            if score > best_score:
                                best_score = score
                                best_call_index = i
                        elif not query and not call_query:
                            # Both are empty - consider it a match
                            best_call_index = i
                            break
                    
                    # If no good match found, fallback to first call
                    if best_call_index is None and task_data['calls']:
                        best_call_index = 0
                        best_score = 0.0
                    
                    if best_call_index is not None:
                        call_data = task_data['calls'][best_call_index]
                        result = call_data.get('result', DEFAULT_LOCATION_RESULT).copy()
                        
                        # Add standard GPS fields if not present
                        if "accuracy" not in result:
                            result["accuracy"] = 10.0
                        if "altitude" not in result:
                            result["altitude"] = 52.0
                        if "timestamp" not in result:
                            result["timestamp"] = "2024-01-15T14:30:00Z"
                        if "location_method" not in result:
                            result["location_method"] = "GPS"
                        if "tool" not in result:
                            result["tool"] = "get_device_location"
                        
                            "method": "task_context",
                            "matched_task_id": current_task_id,
                            "call_index": best_call_index,
                            "task_active": True,
                            "query_used": query,
                            "best_score": best_score,
                            "task_id": current_task_id,
                            "scenario": task_data.get('scenario', 'unknown'),
                            "matched_task": True,
                            "multi_call": True
                        }
                else:
                    # Single call task - use task-level result directly
                    result = task_data.get('result', DEFAULT_LOCATION_RESULT).copy()
                    
                    # Add standard GPS fields if not present
                    if "accuracy" not in result:
                        result["accuracy"] = 10.0
                    if "altitude" not in result:
                        result["altitude"] = 52.0
                    if "timestamp" not in result:
                        result["timestamp"] = "2024-01-15T14:30:00Z"
                    if "location_method" not in result:
                        result["location_method"] = "GPS"
                    if "tool" not in result:
                        result["tool"] = "get_device_location"
                    
                        "method": "task_context",
                        "matched_task_id": current_task_id,
                        "call_index": None,
                        "task_active": True,
                        "query_used": query,
                        "task_id": current_task_id,
                        "scenario": task_data.get('scenario', 'unknown'),
                        "matched_task": True,
                        "multi_call": False
                    }
        
        # Priority 2: Intelligent matching based on query
        if query:
            normalized_query = normalize_query(query)
            task_id, task_data, call_index = find_best_matching_task(normalized_query)
            
            if task_data and "result" in task_data:
                result = task_data["result"].copy()
                
                # Add standard GPS fields if not present
                if "accuracy" not in result:
                    result["accuracy"] = 10.0
                if "altitude" not in result:
                    result["altitude"] = 52.0
                if "timestamp" not in result:
                    result["timestamp"] = "2024-01-15T14:30:00Z"
                if "location_method" not in result:
                    result["location_method"] = "GPS"
                if "tool" not in result:
                    result["tool"] = "get_device_location"
                
                # Add matching information to result (for debugging)
                    "method": "intelligent_matching",
                    "matched_task_id": task_id,
                    "call_index": call_index,
                    "task_active": task_context.is_task_active(),
                    "matched_task": True,
                    "multi_call": call_index is not None
                }
                
        
        # Priority 3: Default fallback response
        result = DEFAULT_LOCATION_RESULT.copy()
        result.update({
            "accuracy": 10.0,
            "altitude": 52.0,
            "timestamp": "2024-01-15T14:30:00Z",
            "address": "San Francisco, CA, USA",
            "location_method": "GPS",
            "tool": "get_device_location"
        })
            "method": "fallback",
            "task_active": task_context.is_task_active(),
            "matched_task": False,
            "multi_call": False,
            "matched_task_id": None
        }
        
        
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Failed to get device location: {str(e)}",
            "tool": "get_device_location"
        }
            "method": "error",
            "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            "matched_task": False,
            "multi_call": False,
            "matched_task_id": None
        }

def normalize_query(query: str) -> str:
    """
    Normalize query string for better matching
    
    Args:
        query: Input query string
    
    Returns:
        Normalized query string
    """
    if not query:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = query.lower().strip()
    
    # Remove extra spaces
    normalized = ' '.join(normalized.split())
    
    # Remove common punctuation
    normalized = normalized.replace(',', ' ').replace('.', ' ').replace('?', ' ').replace('!', ' ')
    normalized = ' '.join(normalized.split())
    
    return normalized

def calculate_call_similarity(call_data: Dict[str, Any], query: str) -> float:
    """
    Calculate similarity between call data and query
    
    Args:
        call_data: Call data containing queries and other info
        query: Query string to match
    
    Returns:
        Similarity score between 0 and 1
    """
    if not call_data:
        return 0.0
    
    call_queries = call_data.get('queries', [])
    if not call_queries:
        return 0.0
    
    best_score = 0.0
    
    for call_query in call_queries:
        normalized_call_query = normalize_query(call_query)
        
        # Calculate multiple similarity metrics
        sequence_sim = SequenceMatcher(None, query, normalized_call_query).ratio()
        word_overlap_sim = calculate_word_overlap_similarity(query, normalized_call_query)
        substring_sim = calculate_substring_similarity(query, normalized_call_query)
        
        # Weighted combination of similarity metrics
        final_score = (sequence_sim * 0.4 + word_overlap_sim * 0.4 + substring_sim * 0.2)
        
        # Bonus for exact substring matches
        if query in normalized_call_query or normalized_call_query in query:
            final_score *= 1.2
        
        # Track best score for this call
        if final_score > best_score:
            best_score = final_score
    
    return best_score

def find_best_matching_task(query: str, call_index: int = None) -> tuple:
    """
    Find the best matching task based on query similarity
    
    Args:
        query: Normalized query string
        call_index: Specific call index to match (optional)
    
    Returns:
        Tuple of (task_id, task_data, call_index) or (None, None, None) if no good match
    """
    best_task_id = None
    best_task_data = None
    best_call_index = None
    best_score = 0.0
    
    # Dynamic threshold based on task context
    if task_context.is_task_active():
        min_threshold = 0.0  # Always return best match when task is active
    else:
        min_threshold = 0.3  # Minimum similarity threshold
    
    for task_id, task_data in TASK_DATA.items():
        # Handle calls structure
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            for idx, call_data in enumerate(task_data['calls']):
                # If specific call_index is requested, only check that call
                if call_index is not None and idx != call_index:
                    continue
                
                call_sim = calculate_call_similarity(call_data, query)
                
                # Update best match if this score is better
                if call_sim > best_score and call_sim >= min_threshold:
                    best_score = call_sim
                    best_task_id = task_id
                    best_task_data = task_data
                    best_call_index = idx
        else:
            # Handle legacy structure (no calls)
            task_best_score = 0.0
            
            for task_query in task_data["queries"]:
                normalized_task_query = normalize_query(task_query)
                
                # Calculate multiple similarity metrics
                sequence_sim = SequenceMatcher(None, query, normalized_task_query).ratio()
                word_overlap_sim = calculate_word_overlap_similarity(query, normalized_task_query)
                substring_sim = calculate_substring_similarity(query, normalized_task_query)
                
                # Weighted combination of similarity metrics
                final_score = (sequence_sim * 0.4 + word_overlap_sim * 0.4 + substring_sim * 0.2)
                
                # Bonus for exact substring matches
                if query in normalized_task_query or normalized_task_query in query:
                    final_score *= 1.2
                
                # Track best score for this task
                if final_score > task_best_score:
                    task_best_score = final_score
            
            # Update global best if this task is better
            if task_best_score > best_score and task_best_score >= min_threshold:
                best_score = task_best_score
                best_task_id = task_id
                best_task_data = task_data
                best_call_index = None  # No call index for legacy structure
    
    return (best_task_id, best_task_data, best_call_index)

def calculate_word_overlap_similarity(query1: str, query2: str) -> float:
    """Calculate word overlap similarity between two queries"""
    if not query1 or not query2:
        return 0.0
    
    words1 = set(query1.split())
    words2 = set(query2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def calculate_substring_similarity(query1: str, query2: str) -> float:
    """Calculate substring similarity between two queries"""
    if not query1 or not query2:
        return 0.0
    
    shorter, longer = (query1, query2) if len(query1) <= len(query2) else (query2, query1)
    
    if shorter in longer:
        return len(shorter) / len(longer)
    
    return 0.0

# Tool registration schema
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_device_location",
        "description": "get_device_location tool - Get device GPS location information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Location query (optional)"
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
        name="get_device_location",
        function=get_device_location,
        schema=TOOL_SCHEMA,
        description="Tool function for get_device_location"
    )

# Auto-register when module is imported
register_tool()
