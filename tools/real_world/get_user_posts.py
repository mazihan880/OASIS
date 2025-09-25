#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_user_posts tool implementation
Retrieve public posts from social media platforms
"""

import json
import random
import re
from typing import Dict, Any, List, Optional
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
    from ..resource.get_user_posts_data import TASK_DATA, DEFAULT_POSTS_RESULT, get_all_usernames
except ImportError:
    try:
        # Try absolute import
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resource_dir = os.path.join(os.path.dirname(current_dir), 'resource')
        sys.path.insert(0, resource_dir)
        from get_user_posts_data import TASK_DATA, DEFAULT_POSTS_RESULT, get_all_usernames
    except ImportError:
        TASK_DATA = {}
        DEFAULT_POSTS_RESULT = {
            "status": "success",
            "posts": [
                {
                    "post_id": "default_001",
                    "date": "2024-01-01",
                    "content": "Posts retrieval completed successfully",
                    "likes": 0,
                    "shares": 0,
                    "comments": 0
                }
            ],
            "total_posts": 1,
            "message": "User posts fetched successfully"
        }
        
        def get_all_usernames():
            return []

def normalize_username(username: str) -> str:
    """
    Normalize username for better matching
    
    Args:
        username: Username to normalize
    
    Returns:
        Normalized username
    """
    if not username:
        return ""
    
    # Remove @ symbol if present
    normalized = username.strip().lower()
    if normalized.startswith('@'):
        normalized = normalized[1:]
    
    # Remove extra spaces and special characters
    normalized = re.sub(r'[^\w\d_]', '', normalized)
    
    return normalized

def normalize_query(query: str) -> str:
    """
    Normalize query string for better matching
    
    Args:
        query: Query string to normalize
    
    Returns:
        Normalized query string
    """
    if not query:
        return ""
    
    # Convert to lowercase
    normalized = query.lower().strip()
    
    # Remove extra spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove common punctuation except @
    normalized = re.sub(r'["\'\.\,\?\!\;\:]', '', normalized)
    
    return normalized

def extract_username_from_query(query: str) -> Optional[str]:
    """
    Extract username from query string
    
    Args:
        query: Query string that may contain username
    
    Returns:
        Extracted username or None
    """
    # Look for @username pattern
    username_match = re.search(r'@(\w+)', query)
    if username_match:
        return username_match.group(1).lower()
    
    # Look for username: pattern
    username_match = re.search(r'username[:\s]+(\w+)', query, re.IGNORECASE)
    if username_match:
        return username_match.group(1).lower()
    
    # Look for user pattern
    username_match = re.search(r'user[:\s]+(\w+)', query, re.IGNORECASE)
    if username_match:
        return username_match.group(1).lower()
    
    return None

def calculate_query_similarity(query1: str, query2: str) -> float:
    """
    Calculate similarity between two queries
    
    Args:
        query1: First query string
        query2: Second query string
    
    Returns:
        Similarity score (0.0 to 1.0)
    """
    if not query1 or not query2:
        return 0.0
    
    # Normalize both queries
    norm1 = normalize_query(query1)
    norm2 = normalize_query(query2)
    
    # Calculate sequence similarity
    seq_similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Calculate word overlap
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return seq_similarity
    
    word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))
    
    # Combine scores
    combined_score = (seq_similarity * 0.6) + (word_overlap * 0.4)
    
    return combined_score

def get_user_posts(*args, **kwargs) -> Dict[str, Any]:
    """
    Retrieve public posts from social media platforms
    
    Args:
        username: Username to search for posts
        
    Returns:
        Dictionary containing posts and metadata
    """
    # Extract username from args or kwargs
    if args:
        username = args[0]
    elif 'username' in kwargs:
        username = kwargs['username']
    else:
        return {
            "status": "error",
            "message": "Username parameter is required",
            "posts": [],
            "total_posts": 0
        }
    # Priority 1: Check if task context is active and has data
    if task_context.is_task_active():
        current_task_id = task_context.get_current_task_id()
        if current_task_id and current_task_id in TASK_DATA:
            task_data = TASK_DATA[current_task_id]
            
            # For multi-call tasks, find the best matching call within the task
            if 'calls' in task_data and isinstance(task_data['calls'], list) and len(task_data['calls']) > 0:
                # Build query string for matching
                def build_query_string(username):
                    return f"{username or ''}".strip().lower()
                
                query_string = build_query_string(username)
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
                result = call_data.get('result', DEFAULT_POSTS_RESULT).copy()
                
                    'method': 'task_context',
                    'matched_task_id': current_task_id,
                    'call_index': best_call_index,
                    'task_active': True,
                    'username_used': username,
                    'best_score': best_score
                }
                return {
                    'result': result,
                }
            else:
                # Single call task - use task-level result directly
                result = task_data.get('result', DEFAULT_POSTS_RESULT).copy()
                
                    'method': 'task_context',
                    'matched_task_id': current_task_id,
                    'call_index': None,
                    'task_active': True
                }
                return {
                    'result': result,
                }
    
    # Priority 2: Fallback to intelligent matching
    # Normalize username
    normalized_username = normalize_username(username)
    
    # Find best matching task
    best_match = find_best_matching_task(normalized_username)
    
    if best_match:
        task_id, similarity_score = best_match
        result = TASK_DATA[task_id]["result"].copy()
        
        # Add debug metadata
            "method": "similarity_match",
            "matched_task_id": task_id,
            "similarity_score": similarity_score,
            "original_username": username,
            "normalized_username": normalized_username,
            "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False
        }
        
        return {
            'result': result,
        }
    
    # No match found, return default result
    result = DEFAULT_POSTS_RESULT.copy()
    
    # Customize default result based on username
    if normalized_username and result.get("posts") and len(result["posts"]) > 0:
        result["posts"][0]["content"] = f"Posts retrieved for user: @{normalized_username}"
        result["message"] = f"Posts fetched successfully for @{normalized_username}"
    
    # Add debug metadata
        "method": "fallback",
        "original_username": username,
        "normalized_username": normalized_username,
        "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False
    }
    
    return {
        'result': result,
    }

def find_best_matching_task(username: str) -> Optional[tuple]:
    """
    Find the best matching task with enhanced similarity calculation
    
    Args:
        username: Normalized username string
    
    Returns:
        (task_id, similarity_score) or None
    """
    best_match = None
    best_score = 0.0
    
    # Dynamic threshold - remove threshold when task context is active
    try:
        task_active = hasattr(task_context, 'is_task_active') and task_context.is_task_active()
    except:
        task_active = False
    
    min_threshold = 0.0 if task_active else 0.8  # Minimum similarity threshold for exact matches
    
    for task_id, task_data in TASK_DATA.items():
        task_best_score = 0.0
        
        # Check against task query (single query, not queries array)
        query_data = task_data.get("query", {})
        if isinstance(query_data, dict) and "username" in query_data:
            task_username = normalize_username(query_data["username"])
            
            # Direct username comparison
            if username == task_username:
                task_best_score = 1.0
            else:
                # Calculate similarity
                similarity = calculate_query_similarity(username, task_username)
                if similarity > task_best_score:
                    task_best_score = similarity
        
        # Update global best score
        if task_best_score > best_score and task_best_score >= min_threshold:
            best_score = task_best_score
            best_match = (task_id, task_best_score)
    
    return best_match

def generate_fallback_response(username: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no match is found
    
    Args:
        username: Original username string
    
    Returns:
        Fallback response dictionary
    """
    result = DEFAULT_POSTS_RESULT.copy()
    
    if username:
        normalized = normalize_username(username)
        result["posts"][0]["content"] = f"Posts retrieved for user: @{normalized}"
        result["message"] = f"Posts fetched successfully for @{normalized}"
    
    return result

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_user_posts",
        "description": "Retrieve public posts from social media platforms",
        "parameters": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Username to search for posts (with or without @ symbol)"
                }
            },
            "required": ["username"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="get_user_posts",
        function=get_user_posts,
        schema=TOOL_SCHEMA,
        description="Tool function for get_user_posts"
    )

# Auto-register when module is imported
register_tool()
