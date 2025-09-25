#!/usr/bin/env python3
"""
get_browser_cookies tool implementation
Extracts browser cookies from specified domains
"""

import json
from typing import Dict, Any, List
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

# Import the data
try:
    from tools.resource.get_browser_cookies_data import TASK_DATA, DEFAULT_COOKIES_RESULT
except ImportError:
    TASK_DATA = {}
    DEFAULT_COOKIES_RESULT = {
        "status": "success",
        "message": "Browser cookies extraction completed",
        "cookies": [],
        "domain": "unknown",
        "extraction_time": "2025-01-01T00:00:00Z"
    }

def calculate_call_similarity(domain: str, call_data: Dict[str, Any]) -> float:
    """
    Calculate similarity score between input and a specific call
    """
    score = 0.0
    
    # Check domain parameter
    if domain and 'domain' in call_data:
        if call_data['domain'].lower() == domain.lower():
            score += 30
    
    return score

def find_best_matching_task(domain: str, call_index: int = None) -> tuple:
    """
    Find the best matching task for the given domain
    
    Args:
        domain: The domain to search for
        call_index: Specific call index to match (optional)
        
    Returns:
        Tuple of (task_id, task_data, call_index) for calls structure or (task_id, task_data, None) for legacy
    """
    if not TASK_DATA:
        return (None, None, None)
    
    best_match = None
    best_score = 0.0
    best_task_id = None
    best_call_index = None
    
    domain_lower = domain.lower().strip()
    
    for task_id, task_data in TASK_DATA.items():
        # Handle calls structure
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            for idx, call_data in enumerate(task_data['calls']):
                # If specific call_index is requested, only check that call
                if call_index is not None and idx != call_index:
                    continue
                
                call_sim = calculate_call_similarity(domain, call_data)
                
                # Process queries in call_data
                queries = call_data.get('queries', [])
                for query in queries:
                    query_lower = query.lower().strip()
                    
                    # Calculate similarity score
                    similarity = SequenceMatcher(None, domain_lower, query_lower).ratio()
                    
                    # Boost score for exact matches
                    if domain_lower == query_lower:
                        similarity += 1.0
                    
                    # Boost score for domain containment
                    if domain_lower in query_lower or query_lower in domain_lower:
                        similarity += 0.5
                    
                    # Add call similarity bonus
                    final_score = similarity + (call_sim * 0.1)
                    
                    if final_score > best_score:
                        best_score = final_score
                        best_match = call_data
                        best_task_id = task_id
                        best_call_index = idx
        
        # Handle legacy structure (no calls)
        else:
            queries = task_data.get('queries', [])
            
            for query in queries:
                query_lower = query.lower().strip()
                
                # Calculate similarity score
                similarity = SequenceMatcher(None, domain_lower, query_lower).ratio()
                
                # Boost score for exact matches
                if domain_lower == query_lower:
                    similarity += 1.0
                
                # Boost score for domain containment
                if domain_lower in query_lower or query_lower in domain_lower:
                    similarity += 0.5
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = task_data
                    best_task_id = task_id
                    best_call_index = None
    
    # Dynamic threshold based on task context
    if task_context.is_task_active():
        threshold = 0.0  # Always return best match when task is active
    else:
        threshold = 1.5  # Require higher similarity for matching
    
    # Use threshold for matching
    if best_score < threshold:
        return (None, {'result': DEFAULT_COOKIES_RESULT}, None)
    
    # For calls structure, return the call data with result
    if best_call_index is not None:
        result_data = {'result': best_match.get('result', best_match)}
        return (best_task_id, result_data, best_call_index)
    
    # For legacy structure, return the task data
    return (best_task_id, best_match, None)

def get_browser_cookies(*args, **kwargs) -> Dict[str, Any]:
    """
    Extract browser cookies from specified domain
    
    Args:
        domain (str): The domain to extract cookies from
        
    Returns:
        Dict containing the extraction result
    """
    try:
        # Handle both positional and keyword arguments
        if args:
            domain = str(args[0])
        elif 'domain' in kwargs:
            domain = str(kwargs['domain'])
        else:
            return {
                "result": {
                    "status": "error",
                    "message": "Domain parameter is required"
                },
                    "method": "parameter_error",
                    "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                    "matched_task": False,
                    "multi_call": False,
                    "matched_task_id": None
                }
            }
        
        # Priority 1: Check if task context is active and has data
        if task_context.is_task_active():
            current_task_id = task_context.get_current_task_id()
            if current_task_id and current_task_id in TASK_DATA:
                task_data = TASK_DATA[current_task_id]
                
                # For multi-call tasks, find the best matching call within the task
                if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                    best_call_index = None
                    best_score = -1
                    
                    def build_query_string(call_data):
                        """Build a query string from call data for similarity comparison"""
                        parts = []
                        if 'domain' in call_data:
                            parts.append(str(call_data['domain']))
                        if 'args' in call_data and 'domain' in call_data['args']:
                            parts.append(str(call_data['args']['domain']))
                        return ' '.join(parts).lower()
                    
                    for i, call_data in enumerate(task_data['calls']):
                        call_query = build_query_string(call_data)
                        
                        # Calculate similarity using SequenceMatcher
                        similarity = SequenceMatcher(None, domain.lower(), call_query).ratio()
                        
                        if similarity > best_score:
                            best_score = similarity
                            best_call_index = i
                    
                    # If no match found, fallback to first call
                    if best_call_index is None:
                        best_call_index = 0
                        best_score = 0.0
                    
                    call_data = task_data['calls'][best_call_index]
                    result = call_data.get('result', DEFAULT_COOKIES_RESULT).copy()
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': best_call_index,
                        'best_score': best_score,
                        'task_active': True,
                        'query_domain': domain,
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
                    result = task_data.get('result', DEFAULT_COOKIES_RESULT).copy()
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': None,
                        'task_active': True,
                        'query_domain': domain,
                        'task_id': current_task_id,
                        'scenario': task_data.get('scenario', 'unknown'),
                        'matched_task': True,
                        'multi_call': False
                    }
                    return {
                        'result': result,
                    }
        
        # Priority 2: Fallback to intelligent matching
        task_id, task_data, call_index = find_best_matching_task(domain)
        
        if task_data and 'result' in task_data:
            result = task_data['result'].copy()
        else:
            result = DEFAULT_COOKIES_RESULT.copy()
        
        # Add debug metadata
            'method': 'similarity_match',
            'matched_task_id': task_id,
            'call_index': call_index,
            'query_domain': domain,
            'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            'matched_task': task_data is not None,
            'multi_call': call_index is not None
        }
        
        return {
            'result': result,
        }
        
    except Exception as e:
        return {
            "result": {
                "status": "error",
                "message": f"Failed to extract browser cookies: {str(e)}",
                "error_code": "COOKIES_EXTRACTION_ERROR"
            },
                "method": "exception_fallback",
                "error": str(e),
                "task_active": False,
                "matched_task": False,
                "multi_call": False,
                "matched_task_id": None
            }
        }

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_browser_cookies",
        "description": "Extract browser cookies from specified domain",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "The domain to extract cookies from (e.g., 'github.com', 'google.com')"
                }
            },
            "required": ["domain"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="get_browser_cookies",
        function=get_browser_cookies,
        schema=TOOL_SCHEMA,
        description="Tool function for get_browser_cookies"
    )

if __name__ == "__main__":
    # Test the tool
    test_cases = [
        "github.com",
        "google.com", 
        "twitter.com",
        "unknown-domain.com"
    ]
    
    for domain in test_cases:
        result = get_browser_cookies(domain=domain)
        if '_match_info' in result:

# Auto-register when module is imported
register_tool()
