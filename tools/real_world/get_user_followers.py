#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_user_followers tool implementation
Get user followers information from social media platforms
"""

import json
import random
import re
from typing import Dict, Any, Optional, List
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
    from ..resource.get_user_followers_data import TASK_DATA, DEFAULT_FOLLOWERS_RESULT, PLATFORM_ALIASES, get_platform_from_query, normalize_followers_query
except ImportError:
    TASK_DATA = {}
    DEFAULT_FOLLOWERS_RESULT = {"status": "success", "message": "User followers query completed", "total_followers": 1250, "followers": []}
    PLATFORM_ALIASES = {
        'twitter': ['twitter', 'x', 'tweet', 'twitter.com', 'x.com'],
        'instagram': ['instagram', 'ig', 'insta', 'instagram.com'],
        'facebook': ['facebook', 'fb', 'facebook.com'],
        'linkedin': ['linkedin', 'linkedin.com'],
        'tiktok': ['tiktok', 'tik tok', 'tiktok.com']
    }
    
    def get_platform_from_query(query):
        return "twitter"
    
    def normalize_followers_query(query):
        return query.lower().strip() if query else ""

def calculate_query_similarity(query1: str, query2: str) -> float:
    """
    Calculate similarity between two queries using sequence matching
    
    Args:
        query1: First query string
        query2: Second query string
    
    Returns:
        Similarity score (0.0 to 1.0)
    """
    if not query1 or not query2:
        return 0.0
    
    # Normalize queries
    norm1 = normalize_followers_query(query1)
    norm2 = normalize_followers_query(query2)
    
    # Calculate sequence similarity
    return SequenceMatcher(None, norm1, norm2).ratio()

def is_valid_username_query(query: str, username: str = None) -> bool:
    """
    Determine if a query is asking for valid user follower information
    
    Args:
        query: Query string to analyze
        username: Username to validate
    
    Returns:
        True if query is valid for user followers, False otherwise
    """
    if not query and not username:
        return False
    
    query_lower = (query or "").lower()
    username_lower = (username or "").lower()
    
    # Valid follower query indicators
    follower_indicators = [
        'followers', 'following', 'follow', 'subscriber', 'fan', 'audience',
        'social', 'twitter', 'instagram', 'facebook', 'linkedin', 'tiktok',
        'profile', 'account', 'user', '@', 'social media'
    ]
    
    # In sandbox environment, be more permissive with usernames
    # Only reject queries that are clearly not about social media followers
    truly_invalid_indicators = [
        'stock price', 'market data', 'financial report', 'investment analysis'
    ]
    
    # Check for valid indicators
    has_valid_indicators = any(indicator in query_lower for indicator in follower_indicators)
    
    # Check for truly invalid indicators (only reject very specific non-social queries)
    has_invalid_indicators = any(indicator in query_lower for indicator in truly_invalid_indicators)
    
    # If username looks like a social media handle, always allow it
    if username:
        if username.startswith('@') or any(char.isalpha() for char in username):
            has_valid_indicators = True
    
    # Check if query contains @ mentions
    if '@' in query_lower:
        has_valid_indicators = True
    
    # In sandbox environment, if we have a username, assume it's valid unless clearly invalid
    if username and not has_invalid_indicators:
        return True
    
    return has_valid_indicators and not has_invalid_indicators

def extract_username_from_query(query: str) -> Optional[str]:
    """
    Extract username from query string
    
    Args:
        query: Query string to analyze
    
    Returns:
        Extracted username or None
    """
    if not query:
        return None
    
    # Look for @username patterns
    at_pattern = r'@([a-zA-Z0-9_]+)'
    at_matches = re.findall(at_pattern, query)
    if at_matches:
        return at_matches[0]
    
    # Look for common username patterns
    username_patterns = [
        r'\b([a-zA-Z0-9_]{3,20})\b',  # General username pattern
        r'user[:\s]+([a-zA-Z0-9_]+)',  # "user: username" pattern
        r'username[:\s]+([a-zA-Z0-9_]+)',  # "username: username" pattern
        r'account[:\s]+([a-zA-Z0-9_]+)',  # "account: username" pattern
    ]
    
    for pattern in username_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            # Filter out common words that aren't usernames
            common_words = {'user', 'account', 'profile', 'followers', 'following', 'get', 'the', 'for', 'from'}
            for match in matches:
                if match.lower() not in common_words and len(match) >= 3:
                    return match
    
    return None

def calculate_followers_priority(task_query: str, username: str = None, platform: str = None) -> float:
    """
    Calculate priority score based on username and platform matching
    
    Args:
        task_query: The task query string to match against
        username: Username to search for
        platform: Social media platform
    
    Returns:
        Priority score (0.0 to 1.0)
    """
    score = 0.0
    
    if not task_query:
        return score
    
    # First check if this is a valid user followers query
    if not is_valid_username_query(task_query, username):
        return 0.0  # Return 0 if this doesn't seem like a valid followers query
    
    query_lower = task_query.lower()
    
    # Check for username matches
    if username:
        username_lower = username.lower()
        if username_lower in query_lower:
            score += 0.5
        
        # Check for @ mentions
        if f"@{username_lower}" in query_lower:
            score += 0.3
    
    # Check for platform matches
    if platform:
        platform_lower = platform.lower()
        if platform_lower in query_lower:
            score += 0.4
        
        # Check platform aliases
        if platform_lower in PLATFORM_ALIASES:
            for alias in PLATFORM_ALIASES[platform_lower]:
                if alias.lower() in query_lower:
                    score += 0.3
                    break
    
    # Check for general follower terms
    follower_terms = ['followers', 'following', 'follow', 'subscriber', 'fan', 'audience', 'social']
    for term in follower_terms:
        if term in query_lower:
            score += 0.1
    
    return min(score, 1.0)

def extract_username_from_query(query: str) -> Optional[str]:
    """
    Extract username from query string
    
    Args:
        query: Query string
    
    Returns:
        Extracted username or None
    """
    if not query:
        return None
    
    # Look for @username pattern
    at_match = re.search(r'@(\w+)', query)
    if at_match:
        return at_match.group(1)
    
    # Look for common username patterns
    username_patterns = [
        r'user[:\s]+(\w+)',
        r'username[:\s]+(\w+)',
        r'account[:\s]+(\w+)',
        r'profile[:\s]+(\w+)'
    ]
    
    for pattern in username_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def get_user_followers(*args, **kwargs) -> Dict[str, Any]:
    """
    Get user followers information from social media platforms
    
    Args:
        username (str, optional): Username to get followers for
        platform (str, optional): Social media platform
        query (str, optional): Query string for matching
        limit (int, optional): Maximum number of followers to return
    
    Returns:
        Dict containing user followers information
    """
    
    # Handle both positional and keyword arguments
    if args:
        if len(args) >= 1:
            username = args[0]
        else:
            username = kwargs.get('username', '')
    else:
        username = kwargs.get('username', '')
    
    platform = kwargs.get('platform', '')
    query = kwargs.get('query', '')
    limit = kwargs.get('limit', 50)
    
    # Create combined query for validation
    combined_query = f"{username} {platform} {query}".strip()
    
    # Validate that this is a proper user followers query
    if combined_query and not is_valid_username_query(combined_query, username):
        return {
            "status": "error",
            "message": "This query does not appear to be asking for user follower information. Please check your query and ensure it's related to social media followers.",
            "error_code": "INVALID_FOLLOWERS_QUERY",
            "query_analyzed": combined_query
        }
    
    # Try to extract username from query if not provided
    if not username and query:
        extracted_username = extract_username_from_query(query)
        if extracted_username:
            username = extracted_username
    
    # If still no username, continue with empty username (mechanism removed)
    
    # Normalize username (remove @ if present)
    if username and username.startswith('@'):
        username = username[1:]
    
    # Determine platform if not provided
    if not platform and query:
        platform = get_platform_from_query(query)
    
    # Default platform
    if not platform:
        platform = "twitter"
    
    # Priority 1: Check if task context is active and has data
    if task_context.is_task_active():
        current_task_id = task_context.get_current_task_id()
        if current_task_id and current_task_id in TASK_DATA:
            task_data = TASK_DATA[current_task_id]
            
            # For multi-call tasks, find the best matching call within the task
            if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                # Build query string for matching
                def build_query_string(username, platform, query):
                    return f"{username or ''} {platform or ''} {query or ''}".strip().lower()
                
                query_string = build_query_string(username, platform, query)
                best_call_index = None
                best_score = -1
                
                # Find best matching call using query similarity
                for i, call_data in enumerate(task_data['calls']):
                    call_queries = call_data.get('queries', [])
                    for call_query in call_queries:
                        score = SequenceMatcher(None, query_string, call_query.lower()).ratio()
                        if score > best_score:
                            best_score = score
                            best_call_index = i
                
                # If no match found, fallback to first call
                if best_call_index is None:
                    best_call_index = 0
                    best_score = 0.0
                
                call_data = task_data['calls'][best_call_index]
                result = call_data.get('result', DEFAULT_FOLLOWERS_RESULT).copy()
                
                # Apply limit if specified
                if 'followers' in result and isinstance(result['followers'], list):
                    result['followers'] = result['followers'][:limit]
                    result['returned_count'] = len(result['followers'])
                
                    'method': 'task_context',
                    'matched_task_id': current_task_id,
                    'call_index': best_call_index,
                    'task_active': True,
                    'best_score': best_score,
                    'task_id': current_task_id,
                    'scenario': task_data.get('scenario', 'unknown'),
                    'matched_task': True,
                    'multi_call': True
                }
                return {
                    'result': result,
                }
            else:
                # Single call task - use task-level result directly
                result = task_data.get('result', DEFAULT_FOLLOWERS_RESULT).copy()
                
                # Apply limit if specified
                if 'followers' in result and isinstance(result['followers'], list):
                    result['followers'] = result['followers'][:limit]
                    result['returned_count'] = len(result['followers'])
                
                    'method': 'task_context',
                    'matched_task_id': current_task_id,
                    'call_index': None,
                    'task_active': True,
                    'task_id': current_task_id,
                    'scenario': task_data.get('scenario', 'unknown'),
                    'matched_task': True,
                    'multi_call': False
                }
                return {
                    'result': result,
                }
    
    # Priority 2: Fallback to intelligent matching
    # Create search query for matching
    search_query = f"{username} {platform} {query}".strip()
    
    # Try to find best matching task
    best_match = find_best_matching_task(search_query, username, platform)
    
    if best_match:
        task_id, task_data, similarity = best_match
        
        # Return the result from matched task
        result = task_data['result'].copy()
        
        # Ensure consistent format
        if 'status' not in result:
            result['status'] = 'success'
        
        # Apply limit if specified
        if 'followers' in result and isinstance(result['followers'], list):
            result['followers'] = result['followers'][:limit]
            result['returned_count'] = len(result['followers'])
        
        # Add debug metadata
            'method': 'similarity_match',
            'matched_task_id': task_id,
            'similarity_score': similarity,
            'search_query': search_query,
            'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            'matched_task': True,
            'multi_call': False
        }
        
        return {
            'result': result,
        }
    
    # No match found, return default result
    return generate_fallback_response(username, platform, limit)

def find_best_matching_task(query: str, username: str = None, platform: str = None) -> Optional[tuple]:
    """
    Find the best matching task for the given query, username, and platform
    
    Args:
        query: Query string to match
        username: Username to search for
        platform: Social media platform
    
    Returns:
        Tuple of (task_id, task_data, similarity_score) or None if no good match
    """
    if not query and not username and not platform:
        return None
    
    best_match = None
    best_score = 0.0
    
    for task_id, task_data in TASK_DATA.items():
        task_queries = task_data.get('queries', [])
        
        # Calculate priority based on username and platform matching
        priority_score = calculate_followers_priority(query, username, platform)
        
        # Calculate query similarity
        max_query_similarity = 0.0
        for task_query in task_queries:
            similarity = calculate_query_similarity(query, task_query)
            max_query_similarity = max(max_query_similarity, similarity)
        
        # Combine scores
        total_score = (priority_score * 0.6) + (max_query_similarity * 0.4)
        
        # Update best match if this score is better
        # When task context is active, remove threshold to always return best match
        threshold = 0.0 if (hasattr(task_context, 'is_task_active') and task_context.is_task_active()) else 0.3
        if total_score > best_score and total_score > threshold:
            best_score = total_score
            best_match = (task_id, task_data, total_score)
    
    return best_match

def normalize_query(query: str) -> str:
    """
    Normalize query string for better matching
    
    Args:
        query: Raw query string
    
    Returns:
        Normalized query string
    """
    if not query:
        return ""
    
    return normalize_followers_query(query)

def generate_fallback_response(username: str = None, platform: str = None, limit: int = 50) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific match is found
    
    Args:
        username: Username
        platform: Social media platform
        limit: Maximum number of followers to return
    
    Returns:
        Default user followers response
    """
    result = DEFAULT_FOLLOWERS_RESULT.copy()
    
    # Customize based on inputs
    if username:
        result['username'] = username
    
    if platform:
        result['platform'] = platform
    
    # Generate some sample followers
    sample_followers = []
    follower_count = min(limit, random.randint(5, 20))
    
    for i in range(follower_count):
        follower = {
            "username": f"user_{random.randint(1000, 9999)}",
            "display_name": f"User {random.randint(1, 999)}",
            "followers_count": random.randint(10, 5000),
            "verified": random.choice([True, False])
        }
        sample_followers.append(follower)
    
    result['followers'] = sample_followers
    result['total_followers'] = random.randint(500, 10000)
    
    # Add platform-specific fields
    if platform == 'twitter' or platform == 'x':
        result['platform'] = 'twitter'
        for follower in result['followers']:
            follower['tweet_count'] = random.randint(10, 1000)
    elif platform == 'instagram':
        result['platform'] = 'instagram'
        for follower in result['followers']:
            follower['posts_count'] = random.randint(5, 500)
    elif platform == 'facebook':
        result['platform'] = 'facebook'
        for follower in result['followers']:
            follower['friends_count'] = random.randint(50, 2000)
    
    # Add debug metadata
        'method': 'fallback',
        'username': username,
        'platform': platform,
        'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
        'matched_task': False,
        'multi_call': False,
        'matched_task_id': None
    }
    
    return {
        'result': result,
    }

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_user_followers",
        "description": "Get user followers information from social media platforms",
        "parameters": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Username to get followers for"
                },
                "platform": {
                    "type": "string",
                    "description": "Social media platform (e.g., 'twitter', 'instagram', 'facebook')"
                },
                "query": {
                    "type": "string",
                    "description": "Query string for matching (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of followers to return (default: 50)",
                    "default": 50
                }
            },
            "required": []
        }
    }
}

def register_tool():
    """Register the tool with the system"""
    from ..tool_registry import registry
    registry.register(
        name="get_user_followers",
        function=get_user_followers,
        schema=TOOL_SCHEMA,
        description="Get user followers information from social media platforms"
    )

# Auto-register when module is imported
register_tool()