#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_url_content tool implementation with task-aware algorithm
Get and extract main text content from given URL using three-tier priority matching
"""

import json
import random
import re
from typing import Dict, Any, Optional
from difflib import SequenceMatcher
from urllib.parse import urlparse, urlunparse

# Import task context manager with fallback
try:
    from ...evaluation.task_context import task_context
except ImportError:
    try:
        from evaluation.task_context import task_context
    except ImportError:
        # Create a dummy task_context for fallback
        class DummytasksContext:
            def is_task_active(self): return False
            def get_current_task_id(self): return None
            def get_task_data(self, task_id): return None
        
        task_context = DummytasksContext()

# Import resource data
# Import TASK_DATA with proper error handling
TASK_DATA = {}
DEFAULT_URL_CONTENT_RESULT = "Content extraction completed successfully."

try:
    from ..resource.get_url_content_data import TASK_DATA as TD
    TASK_DATA = TD
except ImportError as e:
    try:
        # Try absolute import
        from tools.resource.get_url_content_data import TASK_DATA as TD
        TASK_DATA = TD
    except ImportError as e2:
        # If both fail, keep default empty values
        pass
URL_PATTERNS = {
    'wikipedia': ['wiki', 'wikipedia.org', 'en.wikipedia'],
    'github': ['github.com', 'github.io'],
    'arxiv': ['arxiv.org', 'arxiv.pdf'],
    'gutenberg': ['gutenberg.org', 'project gutenberg'],
    'reuters': ['reuters.com', 'reuters news'],
    'forbes': ['forbes.com', 'forbes.'],
    'government': ['.gov', 'government', 'official'],
    'academic': ['.edu', 'university', 'academic'],
    'documentation': ['docs.', 'documentation', 'manual'],
    'news': ['news', 'article', 'press'],
    'blog': ['blog', 'medium.com', 'wordpress'],
    'social': ['twitter.com', 'facebook.com', 'linkedin.com'],
    'video': ['youtube.com', 'vimeo.com', 'video'],
    'pdf': ['.pdf', 'document', 'paper'],
    'api': ['api.', 'rest', 'endpoint']
}

def normalize_url(url: str) -> str:
    """
    Normalize URL by removing protocol, www, and trailing slashes
    
    Args:
        url: URL to normalize
    
    Returns:
        Normalized URL
    """
    if not url:
        return ""
    
    # Remove protocol
    url = re.sub(r'^https?://', '', url.lower().strip())
    
    # Remove www prefix
    url = re.sub(r'^www\.', '', url)
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    return url

def extract_domain(url: str) -> str:
    """
    Extract domain from URL
    
    Args:
        url: URL to extract domain from
    
    Returns:
        Domain name
    """
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www prefix
        domain = re.sub(r'^www\.', '', domain)
        return domain
    except:
        return ""

def urls_match(url1: str, url2: str) -> bool:
    """
    Check if two URLs are equivalent (considering normalization)
    
    Args:
        url1: First URL
        url2: Second URL
    
    Returns:
        True if URLs match, False otherwise
    """
    if not url1 or not url2:
        return False
    
    norm1 = normalize_url(url1)
    norm2 = normalize_url(url2)
    
    return norm1 == norm2

def calculate_url_priority(task_query: str, url: str = None) -> float:
    """
    Calculate priority score based on URL matching
    
    Args:
        task_query: The task query string to match against
        url: URL to fetch content from
    
    Returns:
        Priority score (0.0 to 1.0)
    """
    score = 0.0
    
    if not url:
        return score
    
    query_lower = task_query.lower()
    url_lower = url.lower()
    
    # Exact URL match
    if url_lower in query_lower or normalize_url(url) in normalize_url(query_lower):
        score += 0.8
    
    # Domain match
    domain = extract_domain(url)
    if domain and domain in query_lower:
        score += 0.6
    
    # Check for URL patterns
    for pattern_type, patterns in URL_PATTERNS.items():
        if any(pattern in url_lower for pattern in patterns):
            if pattern_type in query_lower or any(pattern in query_lower for pattern in patterns):
                score += 0.4
                break
    
    # URL pattern keywords
    url_keywords = ['url', 'link', 'website', 'page', 'content', 'fetch', 'get', 'retrieve', 'extract']
    for keyword in url_keywords:
        if keyword in query_lower:
            score += 0.1
            break
    
    return min(score, 1.0)

def get_url_content(*args, **kwargs) -> Dict[str, Any]:
    """
    Get and extract main text content from given URL using three-tier priority matching:
    1. tasks Context Priority: Use active task data when available
    2. Query Intelligence Matching: Smart matching based on URL and query patterns
    3. Default Fallback: Generate generic response when no match found
    
    Args:
        url: URL to fetch content from
    
    Returns:
        Dictionary containing the extracted content or error message
    """
    # Handle both positional and keyword arguments
    if args:
        url = args[0]
    else:
        url = kwargs.get('url', '')
    
    if not url:
        return {
            "result": {
                "status": "error",
                "content": "",
                "url": "",
                "content_type": "text/html",
                "status_code": 400
            }
        }
    
    # Tier 1: tasks Context Priority
    if task_context.is_task_active():
        current_task_id = task_context.get_current_task_id()
        if current_task_id and current_task_id in TASK_DATA:
            task_data = TASK_DATA[current_task_id]
            
            # For multi-call tasks, find the best matching call within the task
            if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                # Build query string for matching
                def build_query_string(url):
                    return f"{url or ''}".strip().lower()
                
                query_string = build_query_string(url)
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
                call_result = call_data.get('result', {})
                if isinstance(call_result, dict):
                    # If result is a dict, use it as the base and wrap in result field
                    result = {
                        "result": call_result.copy()
                    }
                else:
                    # If result is a string (fallback), create proper structure
                    result = {
                        "result": {
                            "status": "success",
                            "content": call_result,
                            "url": call_data.get('url', url),
                            "content_type": "text/html",
                            "status_code": 200
                        }
                    }
                return result
            else:
                # Single call task - use task-level result directly
                task_result = task_data.get('result', {})
                if isinstance(task_result, dict):
                    # If result is a dict, use it as the base and wrap in result field
                    result = {
                        "result": task_result.copy()
                    }
                else:
                    # If result is a string (fallback), create proper structure
                    result = {
                        "result": {
                            "status": "success",
                            "content": task_result,
                            "url": task_data.get('url', url),
                            "content_type": "text/html",
                            "status_code": 200
                        }
                    }
                return result
    
    # Tier 2: Query Intelligence Matching
    # Try exact URL match first
    for task_id, task_data in TASK_DATA.items():
        task_url = task_data.get('url', '')
        if urls_match(url, task_url):
            task_result = task_data.get('result', {})
            if isinstance(task_result, dict):
                return {
                    "result": task_result.copy()
                }
            else:
                return {
                    "result": {
                        "status": "success",
                        "content": task_result,
                        "url": task_url,
                        "content_type": "text/html",
                        "status_code": 200
                    }
                }
    
    # Smart query matching
    query_str = f"get content from {url}"
    matching_task = find_best_matching_task(query_str, url=url)
    
    if matching_task:
        task_id, task_data, call_index = matching_task
        
        # Handle multi-call tasks with calls array
        if 'calls' in task_data and call_index is not None:
            call_data = task_data['calls'][call_index]
            call_result = call_data.get('result', {})
            if isinstance(call_result, dict):
                return {
                    "result": call_result.copy()
                }
            else:
                return {
                    "result": {
                        "status": "success",
                        "content": call_result,
                        "url": call_data.get('url', url),
                        "content_type": "text/html",
                        "status_code": 200
                    }
                }
        else:
            # Handle legacy single task structure
            task_result = task_data.get('result', {})
            if isinstance(task_result, dict):
                return {
                    "result": task_result.copy()
                }
            else:
                return {
                    "result": {
                        "status": "success",
                        "content": task_result,
                        "url": task_data.get('url', url),
                        "content_type": "text/html",
                        "status_code": 200
                    }
                }
    
    # Tier 3: Default Fallback
    return generate_fallback_response(url=url)

def find_best_matching_task(query: str, url: str = None) -> Optional[tuple]:
    """
    Find the best matching task for the given query and URL with multi-task support
    
    Args:
        query: Query string to match
        url: URL to fetch content from
    
    Returns:
        Tuple of (task_id, task_data, call_index) for best match, or None
    """
    if not TASK_DATA:
        return None
    
    best_match = None
    best_score = 0.0
    
    normalized_query = normalize_query(query)
    
    for task_id, task_data in TASK_DATA.items():
        # Handle multi-call tasks with calls array
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            for call_idx, call_data in enumerate(task_data['calls']):
                # Calculate URL-based priority
                url_score = calculate_url_priority(query, url) if url else 0.0
                
                # Calculate query matching score
                query_score = 0.0
                task_queries = call_data.get('queries', [])
                
                for task_query in task_queries:
                    # Exact match
                    if normalized_query == normalize_query(task_query):
                        query_score = max(query_score, 1.0)
                        break
                    
                    # Partial match using sequence matcher
                    similarity = SequenceMatcher(None, normalized_query, normalize_query(task_query)).ratio()
                    query_score = max(query_score, similarity)
                
                # URL exact match bonus
                task_url = call_data.get('url', '')
                if url and urls_match(url, task_url):
                    url_score += 0.5
                
                # Combined score
                total_score = (query_score * 0.6) + (url_score * 0.4)
                
                if total_score > best_score and total_score > 0.3:  # Minimum threshold
                    best_score = total_score
                    best_match = (task_id, task_data, call_idx)
        else:
            # Handle legacy single task structure
            # Calculate URL-based priority
            url_score = calculate_url_priority(query, url) if url else 0.0
            
            # Calculate query matching score
            query_score = 0.0
            task_queries = task_data.get('queries', [])
            
            for task_query in task_queries:
                # Exact match
                if normalized_query == normalize_query(task_query):
                    query_score = max(query_score, 1.0)
                    break
                
                # Partial match using sequence matcher
                similarity = SequenceMatcher(None, normalized_query, normalize_query(task_query)).ratio()
                query_score = max(query_score, similarity)
            
            # URL exact match bonus
            task_url = task_data.get('url', '')
            if url and urls_match(url, task_url):
                url_score += 0.5
            
            # Combined score
            total_score = (query_score * 0.6) + (url_score * 0.4)
            
            if total_score > best_score and total_score > 0.3:  # Minimum threshold
                best_score = total_score
                best_match = (task_id, task_data, None)
    
    return best_match

def normalize_query(query: str) -> str:
    """Normalize query string for better matching"""
    if not query:
        return ""
    
    # Convert to lowercase and remove extra whitespace
    normalized = re.sub(r'\s+', ' ', query.lower().strip())
    
    # Remove common URL prefixes
    normalized = re.sub(r'^(get content from|fetch|retrieve|extract text from|scrape|read|download|access|visit)\s*', '', normalized)
    
    return normalized

def generate_fallback_response(url: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no matching task is found
    
    Args:
        url: URL that was requested
    
    Returns:
        Fallback response dictionary
    """
    if not url:
        return {
            "result": {
                "status": "error",
                "content": "",
                "url": "",
                "content_type": "text/html",
                "status_code": 400
            }
        }
    
    # Extract domain for generic response
    domain = extract_domain(url)
    
    # Generate generic content based on domain
    if 'wikipedia' in domain:
        content = f"Wikipedia article content from {url}. This page contains encyclopedic information on the requested topic with references and citations."
    elif 'github' in domain:
        content = f"GitHub repository or file content from {url}. This may include source code, documentation, or project information."
    elif 'stackoverflow' in domain:
        content = f"Stack Overflow question and answers from {url}. This page contains programming-related discussions and solutions."
    elif 'reddit' in domain:
        content = f"Reddit post and comments from {url}. This page contains community discussions and user-generated content."
    else:
        content = f"Web page content from {url}. The page contains text, articles, or other information relevant to the requested URL."
    
    return {
        "result": {
            "status": "success",
            "content": content,
            "url": url,
            "content_type": "text/html",
            "status_code": 200
        }
    }

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_url_content",
        "description": "Retrieves the full text content from a single, specific URL that is already known. Use this tool for deep reading of a webpage. **RULE: Use this tool ONLY when the URL is explicitly provided in the user's prompt or has been obtained from a tool OTHER THAN 'web_search'. Do not use this to 'check' or 'explore' search results.**",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch content from"
                }
            },
            "required": ["url"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="get_url_content",
        function=get_url_content,
        schema=TOOL_SCHEMA,
        description="Tool function for get_url_content"
    )

# Auto-register when module is imported
register_tool()
