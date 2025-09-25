#!/usr/bin/env python3
"""
Get User Profile Tool - tasks-aware version
Retrieves public profile information for users on specified platforms
"""

import re
import random
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
            def get_current_task_data(self):
                return None
            def is_task_active(self):
                return False
        task_context = DummytasksContext()

# Import resource data
try:
    # Try relative import first
    from ..resource.get_user_profile_data import TASK_DATA
except ImportError:
    try:
        # Try absolute import as fallback
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resource_dir = os.path.join(current_dir, '..', 'resource')
        sys.path.insert(0, resource_dir)
        from get_user_profile_data import TASK_DATA
    except ImportError:
        # Set empty data if all imports fail
        TASK_DATA = {}

# Set default result
DEFAULT_PROFILE_RESULT = {"status": "error", "message": "Resource data not available"}

def get_user_profile(*args, **kwargs) -> Dict[str, Any]:
    """
    Retrieve public profile information for a user on specified platform - tasks-aware version
    Prioritize data from task context, fallback to smart matching if not exists
    
    Args:
        *args: Positional arguments (username, platform, etc.)
        **kwargs: Keyword arguments (username, platform, user_id, etc.)
    
    Returns:
        Dictionary containing the user profile information
    """
    
    try:
        # Extract profile parameters
        username = None
        platform = None
        user_id = None
        
        # Handle positional arguments
        if len(args) >= 1:
            username = str(args[0])
        if len(args) >= 2:
            platform = str(args[1])
        if len(args) >= 3:
            user_id = str(args[2])
        
        # Handle keyword arguments
        if 'username' in kwargs:
            username = str(kwargs['username'])
        if 'platform' in kwargs:
            platform = str(kwargs['platform'])
        if 'user_id' in kwargs:
            user_id = str(kwargs['user_id'])
        if 'handle' in kwargs:
            username = str(kwargs['handle'])
        if 'account' in kwargs:
            username = str(kwargs['account'])
        
        # Check for task context first (priority)
        current_task_id = task_context.get_current_task_id()
        if current_task_id and task_context.is_task_active() and current_task_id in TASK_DATA:
            task_data = TASK_DATA[current_task_id]
            
            # For multi-call tasks, find the best matching call within the task
            if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                # Build query string for matching
                def build_query_string(username, platform):
                    parts = []
                    if username:
                        parts.append(username.strip())
                    if platform:
                        parts.append(platform.strip())
                    return " ".join(parts).lower()
                
                query_string = build_query_string(username, platform)
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
                result = call_data.get('result', DEFAULT_PROFILE_RESULT).copy()
                    'method': 'task_context',
                    'matched_task_id': current_task_id,
                    'call_index': best_call_index,
                    'task_active': True,
                    'username_used': username,
                    'platform_used': platform,
                    'best_score': best_score,
                    'task_id': current_task_id,
                    'scenario': task_data.get('scenario', 'unknown'),
                    'matched_task': True,
                    'multi_call': True
                }
            else:
                # Single call task - use task-level result directly
                result = task_data.get('result', DEFAULT_PROFILE_RESULT).copy()
                    'method': 'task_context',
                    'matched_task_id': current_task_id,
                    'call_index': None,
                    'task_active': True,
                    'task_id': current_task_id,
                    'scenario': task_data.get('scenario', 'unknown'),
                    'matched_task': True,
                    'multi_call': False
                }
        
        # Fallback to intelligent matching
        # Create search query from profile parameters
        query_parts = []
        if username:
            query_parts.append(username)
        if platform:
            query_parts.append(platform)
        if user_id:
            query_parts.append(user_id)
        
        search_query = " ".join(query_parts) if query_parts else "user profile"
        
        # Find best matching task
        best_match = find_best_matching_task(search_query, username, platform)
        
        if best_match:
            task_id, task_data, call_index = best_match
            
            # Handle multi-call tasks with calls array
            if 'calls' in task_data and call_index is not None:
                call_data = task_data['calls'][call_index]
                result = call_data.get("result", DEFAULT_PROFILE_RESULT).copy()
                    "method": "similarity_match",
                    "matched_task_id": task_id,
                    "call_index": call_index,
                    "original_query": search_query,
                    "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                    "matched_task": True,
                    "multi_call": True
                }
            else:
                # Handle legacy single task structure
                result = task_data.get("result", DEFAULT_PROFILE_RESULT).copy()
                    "method": "similarity_match",
                    "matched_task_id": task_id,
                    "original_query": search_query,
                    "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                    "matched_task": True,
                    "multi_call": False
                }
        
        # No match found, return fallback response
        result = generate_fallback_response(username, platform, user_id)
            'method': 'default_fallback',
            'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            'matched_task': False,
            'multi_call': False,
            'matched_task_id': None
        }
            
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Failed to retrieve user profile: {str(e)}",
            "tool": "get_user_profile"
        }
            "method": "error",
            "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            "matched_task": False,
            "multi_call": False,
            "matched_task_id": None,
            "error": str(e)
        }

def find_best_matching_task(query: str, username: str = None, platform: str = None) -> Optional[tuple]:
    """
    Find the best matching task for the given query with multi-task support
    
    Args:
        query: Search query string
        username: Username to search for
        platform: Platform name
    
    Returns:
        Tuple of (task_id, task_data, call_index) if match found, None otherwise
    """
    
    if not TASK_DATA:
        return None
    
    # Normalize query
    normalized_query = normalize_query(query)
    
    # Find best matching task using improved similarity
    best_match = None
    best_score = 0.0
    
    # Dynamic threshold - remove threshold when task context is active
    try:
        task_active = hasattr(task_context, 'is_task_active') and task_context.is_task_active()
    except:
        task_active = False
    
    min_threshold = 0.0 if task_active else 0.25  # Threshold for matching
    
    # Extract key components for better matching
    search_words = set(normalized_query.split())
    
    for task_id, task_data in TASK_DATA.items():
        if task_id == "default_profile":
            continue
        
        # Handle multi-call tasks with calls array
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            for call_idx, call_data in enumerate(task_data['calls']):
                queries = call_data.get('queries', [])
                if not queries:
                    continue
                    
                for task_query in queries:
                    if not task_query:
                        continue
                        
                    normalized_task_query = normalize_query(task_query)
                    query_words = set(normalized_task_query.split())
                    
                    # Calculate base similarity
                    score = SequenceMatcher(None, normalized_query, normalized_task_query).ratio()
                    
                    # Exact match gets highest priority
                    if normalized_query == normalized_task_query:
                        score = 1.0
                    # Substring match bonus
                    elif normalized_query in normalized_task_query or normalized_task_query in normalized_query:
                        score += 0.2
                    
                    # Word overlap scoring
                    common_words = search_words & query_words
                    if common_words and len(common_words) >= 1:
                        overlap_ratio = len(common_words) / max(len(search_words), len(query_words))
                        if overlap_ratio >= 0.3:
                            score += 0.3 * overlap_ratio
                    
                    # Keyword matching for usernames
                    if username and score > best_score and score >= min_threshold:
                        best_match = (task_id, task_data, call_idx)
                        best_score = score
        else:
            # Handle legacy single task structure
            queries = task_data.get('queries', [])
            if not queries:
                continue
                
            for task_query in queries:
                if not task_query:
                    continue
                    
                normalized_task_query = normalize_query(task_query)
                query_words = set(normalized_task_query.split())
                
                # Calculate base similarity
                score = SequenceMatcher(None, normalized_query, normalized_task_query).ratio()
                
                # Exact match gets highest priority
                if normalized_query == normalized_task_query:
                    score = 1.0
                # Substring match bonus
                elif normalized_query in normalized_task_query or normalized_task_query in normalized_query:
                    score += 0.2
                
                # Word overlap scoring
                common_words = search_words & query_words
                if common_words and len(common_words) >= 1:
                    overlap_ratio = len(common_words) / max(len(search_words), len(query_words))
                    if overlap_ratio >= 0.3:
                        score += 0.3 * overlap_ratio
                
                # Keyword matching for usernames
                if username:
                    username_clean = username.strip('@')
                    if username_clean.lower() in normalized_task_query:
                        score += 0.4
                    # Handle partial username matches
                    if any(username_clean.lower() in word for word in query_words):
                        score += 0.2
                
                # Platform matching bonus
                if platform and platform.lower() in normalized_task_query:
                    score += 0.3
                
                # Special patterns for social media handles
                if username and username.startswith('@'):
                    handle_pattern = f"@{username_clean}"
                    if handle_pattern.lower() in normalized_task_query:
                        score += 0.5
                
                # Update best match if this score is better
                if score > best_score and score >= min_threshold:
                    best_match = (task_id, task_data, None)
                    best_score = score
    
    return best_match

def normalize_query(query: str) -> str:
    """Normalize query string"""
    # Convert to lowercase and remove extra spaces
    normalized = re.sub(r'\s+', ' ', query.lower().strip())
    # Remove common punctuation and special characters
    normalized = re.sub(r'["\'\.\,\?\!\;\:\`\*\n\r]', '', normalized)
    # Remove extra whitespace
    normalized = normalized.strip()
    return normalized

def generate_fallback_response(username: str = None, platform: str = None, 
                             user_id: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific match is found
    
    Args:
        username: Username
        platform: Platform name
        user_id: User ID
    
    Returns:
        Dict containing fallback profile response
    """
    
    response = {
        "status": "success",
        "profile": {
            "username": username or "user_profile",
            "full_name": "User Profile",
            "bio": "Profile information retrieved successfully.",
            "profile_picture_url": "https://example.com/images/default_avatar.jpg"
        },
        "tool": "get_user_profile"
    }
    
    if platform:
        response['platform'] = platform
    if user_id:
        response['profile']['user_id'] = user_id
    
    # Generate contextual responses based on content
    if username:
        if username.startswith('@'):
            response['profile']['display_name'] = username[1:].replace('_', ' ').title()
        
        # Add follower count for social media profiles
        if platform and platform.lower() in ['twitter', 'x', 'instagram', 'tiktok']:
            response['profile']['followers_count'] = random.randint(100, 10000)
            response['profile']['following_count'] = random.randint(50, 1000)
        
        # Add professional info for LinkedIn
        if platform and platform.lower() == 'linkedin':
            response['profile']['headline'] = "Professional Profile"
            response['profile']['connections'] = random.randint(100, 500)
    
    return response

# Tool registration schema
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_user_profile",
        "description": "Retrieve user's public profile for users on specified platforms",
        "parameters": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Username or handle to search for"
                },
                "platform": {
                    "type": "string",
                    "description": "Platform name (e.g., Twitter, Instagram, LinkedIn)"
                },
                "user_id": {
                    "type": "string",
                    "description": "User ID if available"
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
        name="get_user_profile",
        function=get_user_profile,
        schema=TOOL_SCHEMA,
        description="Retrieve public profile information for users on specified platforms"
    )

# Auto-register when module is imported
register_tool()