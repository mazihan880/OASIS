#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filter_contacts tool implementation
Filter contact list based on specified criteria
"""

import json
import random
import re
import time
from typing import Dict, Any, Optional, List, Tuple
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
    from ..resource.filter_contacts_data import TASK_DATA
except ImportError:
    try:
        from tools.resource.filter_contacts_data import TASK_DATA
    except ImportError:
        # Create fallback empty data
        TASK_DATA = {}

# FILTER_CRITERIA is not used in this implementation, so we don't need to import it
FILTER_CRITERIA = {}

DEFAULT_FILTER_RESULT = {
    "status": "success",
    "message": "Contact filtering completed successfully",
    "filtered_contacts": []
}

def filter_contacts(*args, **kwargs) -> Dict[str, Any]:
    """
    Filter contact list based on specified criteria
    
    Args:
        *args: Positional arguments (contacts, criteria)
        **kwargs: Keyword arguments (contacts, criteria, filter, group, etc.)
    
    Returns:
        Dict containing the filtered contact results
    """
    
    try:
        # Priority 1: Check if task context is active and has data
        if task_context.is_task_active():
            current_task_id = task_context.get_current_task_id()
            if current_task_id and current_task_id in TASK_DATA:
                task_data = TASK_DATA[current_task_id]
                
                # For multi-call tasks, return the first call's result (or could be enhanced to match specific calls)
                if 'calls' in task_data and isinstance(task_data['calls'], list) and len(task_data['calls']) > 0:
                    # Use the first call's result for simplicity
                    call_data = task_data['calls'][0]
                    result = call_data.get('result', DEFAULT_FILTER_RESULT).copy()
                    
                        'method': 'task_context_direct',
                        'matched_task_id': current_task_id,
                        'call_index': 0,
                        'task_active': True,
                        'note': 'Direct task ID match - no threshold applied'
                    }
                else:
                    # Single call task - use task-level result directly
                    result = task_data.get('result', DEFAULT_FILTER_RESULT).copy()
                        'method': 'task_context_direct',
                        'matched_task_id': current_task_id,
                        'call_index': None,
                        'task_active': True,
                        'note': 'Direct task ID match - no threshold applied'
                    }
        
        # Priority 2: Check all task data for direct task ID match (in case task_context is not active)
        # Extract and normalize parameters to potentially extract task ID from them
        normalized_params = normalize_parameters(*args, **kwargs)
        
        # Try to find any task that matches exactly by ID
        for task_id, task_data in TASK_DATA.items():
            # Direct task ID match - return immediately without any threshold check
            if 'calls' in task_data and isinstance(task_data['calls'], list) and len(task_data['calls']) > 0:
                # Use the first call's result
                call_data = task_data['calls'][0]
                result = call_data.get('result', DEFAULT_FILTER_RESULT).copy()
                
                    'method': 'direct_task_match',
                    'matched_task_id': task_id,
                    'call_index': 0,
                    'task_active': False,
                    'note': 'Direct task ID match from TASK_DATA - no threshold applied'
                }
                # Only return if this seems like a reasonable match
                # For now, we'll continue to the fallback logic
                break
            else:
                # Single call task
                result = task_data.get('result', DEFAULT_FILTER_RESULT).copy()
                    'method': 'direct_task_match',
                    'matched_task_id': task_id,
                    'call_index': None,
                    'task_active': False,
                    'note': 'Direct task ID match from TASK_DATA - no threshold applied'
                }
                # Only return if this seems like a reasonable match
                # For now, we'll continue to the fallback logic
                break
        
        # Priority 3: Fallback to intelligent matching (keeping original logic as backup)
        # Build query string for matching
        query_string = build_query_string(normalized_params)
        
        # Try to find matching task data without threshold restriction
        task_id, task_data, call_index = find_best_matching_task_no_threshold(query_string, normalized_params)
        
        if task_data:
            # Handle calls structure
            if call_index is not None and 'calls' in task_data:
                call_data = task_data['calls'][call_index]
                result = call_data.get('result', {}).copy()
            else:
                # Handle legacy structure
                result = task_data.get("result", {}).copy()
            
            # Add debug metadata
                "method": "similarity_match_no_threshold",
                "matched_task_id": task_id,
                "call_index": call_index,
                "matched_query": query_string,
                "matched_params": normalized_params,
                "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                "note": "No threshold applied - best match returned"
            }
            
        
        # If no specific task matches, return default response
        return generate_fallback_response(normalized_params)
        
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Error filtering contacts: {str(e)}",
            "filtered_contacts": [],
            "error_details": str(e)
        }
            "method": "exception_fallback",
            "error": str(e),
            "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False
        }

def normalize_parameters(*args, **kwargs) -> Dict[str, Any]:
    """
    Normalize and extract parameters from various input formats
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Dict containing normalized parameters
    """
    
    params = {}
    
    # Handle positional arguments
    if args:
        if len(args) >= 1 and isinstance(args[0], str):
            # First arg could be group_filter or contact_filter
            if any(keyword in args[0].lower() for keyword in ['family', 'friends', 'colleagues', 'group', 'club', 'buddies']):
                params['group_filter'] = args[0]
            else:
                params['contact_filter'] = args[0]
        if len(args) >= 2 and isinstance(args[1], str):
            params['contact_filter'] = args[1]
    
    # Handle keyword arguments - map old parameter names to new ones
    for key, value in kwargs.items():
        if key in ['group_filter']:
            params['group_filter'] = value
        elif key in ['contact_filter']:
            params['contact_filter'] = value
        elif key in ['group', 'group_name', 'groups']:
            params['group_filter'] = value
        elif key in ['contact_name', 'name', 'email', 'department', 'phone']:
            params['contact_filter'] = value
        elif key in ['recently_added'] and value:
            params['contact_filter'] = 'recently_added'
        elif key in ['criteria', 'filter']:
            # Handle complex criteria objects
            if isinstance(value, dict):
                for criteria_key, criteria_value in value.items():
                    if criteria_key in ['group', 'group_name', 'groups']:
                        params['group_filter'] = criteria_value
                    elif criteria_key in ['name', 'contact_name', 'email', 'department']:
                        params['contact_filter'] = criteria_value
            elif isinstance(value, str):
                # Try to parse string criteria
                parsed = parse_parameter_string(value)
                if parsed:
                    for parsed_key, parsed_value in parsed.items():
                        if parsed_key in ['group', 'group_name']:
                            params['group_filter'] = parsed_value
                        else:
                            params['contact_filter'] = parsed_value
    
    return params

def parse_parameter_string(param_str: str) -> Dict[str, Any]:
    """
    Parse parameter strings in various formats
    
    Args:
        param_str: Parameter string to parse
    
    Returns:
        Dict of parsed parameters
    """
    params = {}
    
    # Pattern for "key: value" format
    key_value_pattern = r'(\w+)\s*:\s*(.+?)(?=\s+\w+\s*:|$)'
    matches = re.findall(key_value_pattern, param_str, re.IGNORECASE)
    
    for key, value in matches:
        normalized_key = normalize_parameter_name(key.strip())
        normalized_value = value.strip().strip('"\'')
        
        # Handle boolean values
        if normalized_value.lower() in ['true', 'false']:
            normalized_value = normalized_value.lower() == 'true'
        
        params[normalized_key] = normalized_value
    
    # If no key-value pairs found, treat as a simple value
    if not params:
        # Try to infer parameter type from common patterns
        param_lower = param_str.lower().strip()
        
        # Check if it's an email
        if '@' in param_str and '.' in param_str:
            params['email'] = param_str.strip()
        # Check if it's a group name (common groups)
        elif any(group in param_lower for group in ['family', 'friends', 'work', 'college', 'book', 'neighbors']):
            params['group'] = param_str.strip()
        # Check if it's a name (contains spaces and letters)
        elif ' ' in param_str and param_str.replace(' ', '').isalpha():
            params['name'] = param_str.strip()
        else:
            # Default to treating as a general search term
            params['search_term'] = param_str.strip()
    
    return params

def normalize_parameter_name(param_name: str) -> str:
    """
    Normalize parameter names to standard forms
    
    Args:
        param_name: Original parameter name
    
    Returns:
        Normalized parameter name
    """
    param_lower = param_name.lower().strip()
    
    # Map various parameter names to standard forms
    name_mappings = {
        'group_name': 'group',
        'groups': 'group',
        'contact_name': 'name',
        'full_name': 'name',
        'email_address': 'email',
        'phone_number': 'phone',
        'mobile': 'phone',
        'dept': 'department',
        'vip_status': 'vip',
        'tier': 'vip',
        'last_contact': 'last_contacted',
        'recent_contact': 'last_contacted',
        'total_spent': 'spending',
        'purchase_amount': 'spending',
        'recent': 'recently_added',
        'new': 'recently_added'
    }
    
    return name_mappings.get(param_lower, param_lower)

def build_query_string(params: Dict[str, Any]) -> str:
    """
    Build a query string from normalized parameters
    
    Args:
        params: Normalized parameters
    
    Returns:
        Query string for matching
    """
    query_parts = []
    
    # Handle group_filter
    if 'group_filter' in params and params['group_filter']:
        query_parts.append(f"group_name: {params['group_filter']}")
    
    # Handle contact_filter
    if 'contact_filter' in params and params['contact_filter']:
        contact_value = params['contact_filter']
        if contact_value == 'recently_added':
            query_parts.append("recently_added: true")
        elif '@' in contact_value:  # Email
            query_parts.append(f"email: {contact_value}")
        else:  # Name or department
            query_parts.append(f"contact_name: {contact_value}")
    
    return " ".join(query_parts)

def calculate_call_similarity(query: str, params: Dict[str, Any], call_data: Dict[str, Any]) -> float:
    """
    Calculate similarity score between input and a specific call
    """
    score = 0.0
    
    # Check query parameters
    if 'group_filter' in call_data and 'group_filter' in params:
        if call_data['group_filter'].lower() == params['group_filter'].lower():
            score += 20
    
    if 'contact_filter' in call_data and 'contact_filter' in params:
        if call_data['contact_filter'].lower() in params['contact_filter'].lower():
            score += 15
    
    # Check query string similarity
    if 'query' in call_data:
        similarity = SequenceMatcher(None, query.lower(), call_data['query'].lower()).ratio()
        score += similarity * 10
    
    return score

def find_best_matching_task(query: str, params: Dict[str, Any], call_index: int = None) -> tuple:
    """
    Find the best matching task for the given query and parameters
    
    Args:
        query: Query string to search for
        params: Normalized parameters
        call_index: Specific call index to match (optional)
    
    Returns:
        Tuple of (task_id, task_data, call_index) for calls structure or (task_id, task_data, None) for legacy
    """
    
    best_match = None
    best_score = 0.0
    best_task_id = None
    best_call_index = None
    
    for task_id, task_data in TASK_DATA.items():
        # Check if task has calls structure
        if 'calls' in task_data and isinstance(task_data['calls'], list) and len(task_data['calls']) > 0:
            # Handle calls structure
            for call_idx, call_data in enumerate(task_data['calls']):
                if call_index is not None and call_idx != call_index:
                    continue
                    
                score = calculate_call_similarity(query, params, call_data)
                
                if score > best_score:
                    best_score = score
                    best_match = task_data
                    best_task_id = task_id
                    best_call_index = call_idx
        else:
            # Handle legacy structure
            queries = task_data.get("queries", [])
            
            # Calculate multiple scoring methods
            scores = []
            
            # 1. Direct parameter matching
            param_score = calculate_parameter_match_score(params, queries)
            scores.append(param_score)
            
            # 2. Query string similarity
            for task_query in queries:
                similarity = SequenceMatcher(None, query.lower(), task_query.lower()).ratio()
                scores.append(similarity)
            
            # 3. Keyword matching
            keyword_score = calculate_keyword_match_score(query, queries)
            scores.append(keyword_score)
            
            # 4. Value matching (exact value matches)
            value_score = calculate_value_match_score(params, queries)
            scores.append(value_score)
            
            # Take the maximum score
            max_score = max(scores) if scores else 0.0
            
            if max_score > best_score:
                best_score = max_score
                best_match = task_data
                best_task_id = task_id
                best_call_index = None
    
    # Return best match if score is high enough
    if best_score > 0.4:  # Lowered threshold for better matching
        return best_task_id, best_match, best_call_index
    
    return None, None, None

def find_best_matching_task_no_threshold(query: str, params: Dict[str, Any], call_index: int = None) -> tuple:
    """
    Find the best matching task for the given query and parameters WITHOUT threshold restriction
    
    Args:
        query: Query string to search for
        params: Normalized parameters
        call_index: Specific call index to match (optional)
    
    Returns:
        Tuple of (task_id, task_data, call_index) for calls structure or (task_id, task_data, None) for legacy
    """
    
    best_match = None
    best_score = 0.0
    best_task_id = None
    best_call_index = None
    
    for task_id, task_data in TASK_DATA.items():
        # Check if task has calls structure
        if 'calls' in task_data and isinstance(task_data['calls'], list) and len(task_data['calls']) > 0:
            # Handle calls structure
            for call_idx, call_data in enumerate(task_data['calls']):
                if call_index is not None and call_idx != call_index:
                    continue
                    
                score = calculate_call_similarity(query, params, call_data)
                
                if score > best_score:
                    best_score = score
                    best_match = task_data
                    best_task_id = task_id
                    best_call_index = call_idx
        else:
            # Handle legacy structure
            queries = task_data.get("queries", [])
            
            # Calculate multiple scoring methods
            scores = []
            
            # 1. Direct parameter matching
            param_score = calculate_parameter_match_score(params, queries)
            scores.append(param_score)
            
            # 2. Query string similarity
            for task_query in queries:
                similarity = SequenceMatcher(None, query.lower(), task_query.lower()).ratio()
                scores.append(similarity)
            
            # 3. Keyword matching
            keyword_score = calculate_keyword_match_score(query, queries)
            scores.append(keyword_score)
            
            # 4. Value matching (exact value matches)
            value_score = calculate_value_match_score(params, queries)
            scores.append(value_score)
            
            # Take the maximum score
            max_score = max(scores) if scores else 0.0
            
            if max_score > best_score:
                best_score = max_score
                best_match = task_data
                best_task_id = task_id
                best_call_index = None
    
    # Return best match regardless of score (NO THRESHOLD)
    if best_match is not None:
        return best_task_id, best_match, best_call_index
    
    return None, None, None

def calculate_parameter_match_score(params: Dict[str, Any], queries: List[str]) -> float:
    """
    Calculate score based on parameter matching
    """
    if not params:
        return 0.0
    
    max_score = 0.0
    
    for query in queries:
        score = 0.0
        total_params = len(params)
        
        for key, value in params.items():
            if key in ['contacts', 'criteria', 'filter', 'search_term']:
                continue
            
            # Check if parameter appears in query
            if f"{key}:" in query.lower() or key in query.lower():
                score += 0.5
                
                # Check if value also matches
                if str(value).lower() in query.lower():
                    score += 0.5
        
        if total_params > 0:
            normalized_score = score / total_params
            max_score = max(max_score, normalized_score)
    
    return max_score

def calculate_keyword_match_score(query: str, queries: List[str]) -> float:
    """
    Calculate score based on keyword matching
    """
    keywords = extract_filter_keywords(query)
    if not keywords:
        return 0.0
    
    max_score = 0.0
    
    for task_query in queries:
        task_query_lower = task_query.lower()
        matched_keywords = sum(1 for keyword in keywords if keyword in task_query_lower)
        
        if matched_keywords > 0:
            score = matched_keywords / len(keywords)
            max_score = max(max_score, score)
    
    return max_score

def calculate_value_match_score(params: Dict[str, Any], queries: List[str]) -> float:
    """
    Calculate score based on exact value matching
    """
    if not params:
        return 0.0
    
    max_score = 0.0
    
    for query in queries:
        query_lower = query.lower()
        matched_values = 0
        total_values = 0
        
        for key, value in params.items():
            if key in ['contacts', 'criteria', 'filter']:
                continue
            
            total_values += 1
            value_str = str(value).lower()
            
            # Check for exact value match
            if value_str in query_lower:
                matched_values += 1
        
        if total_values > 0:
            score = matched_values / total_values
            max_score = max(max_score, score)
    
    return max_score

def extract_filter_keywords(query: str) -> List[str]:
    """
    Extract filter keywords from query string
    
    Args:
        query: Query string
    
    Returns:
        List of filter keywords
    """
    
    keywords = []
    
    # Enhanced filter patterns
    filter_patterns = [
        r'group[_\s]*name["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'group["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'groups["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'contact[_\s]*name["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'name["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'email[_\s]*address["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'email["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'department["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'dept["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'vip[_\s]*status["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'vip["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'tier["\s]*:?\s*["\']?([^"\'}\],]+)',
        r'recently[_\s]*added["\s]*:?\s*["\']?([^"\'}\],]+)',
    ]
    
    for pattern in filter_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        keywords.extend([match.strip().lower() for match in matches])
    
    # Also look for common group names and values
    common_values = [
        'family', 'friends', 'work', 'colleagues', 'college', 'high school',
        'book club', 'book lovers', 'vip customers', 'models', 'study group',
        'wholesale', 'corporate', 'influencer', 'collector', 'medical',
        'neighbors', 'alumni', 'gym buddies', 'd&d group', 'marketing'
    ]
    
    query_lower = query.lower()
    for value in common_values:
        if value in query_lower:
            keywords.append(value)
    
    return list(set(keywords))  # Remove duplicates

def generate_fallback_response(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific task matches
    
    Args:
        params: Normalized parameters
    
    Returns:
        Default response with simulated contact data
    """
    
    # Generate some realistic fallback contacts based on parameters
    fallback_contacts = []
    
    if 'group' in params:
        group_name = params['group']
        fallback_contacts = [
            {
                "name": f"Contact from {group_name}",
                "email": f"contact@{group_name.lower().replace(' ', '')}.com",
                "groups": [group_name]
            }
        ]
    elif 'name' in params:
        contact_name = params['name']
        fallback_contacts = [
            {
                "name": contact_name,
                "email": f"{contact_name.lower().replace(' ', '.')}@example.com",
                "groups": ["Contacts"]
            }
        ]
    elif 'email' in params:
        email = params['email']
        fallback_contacts = [
            {
                "name": "Contact",
                "email": email,
                "groups": ["Contacts"]
            }
        ]
    
    result = {
        "status": "success",
        "message": "Contact filtering completed (fallback response)",
        "filtered_contacts": fallback_contacts
    }
    
    # Add debug metadata
        'method': 'fallback',
        'matched_params': params,
        'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False
    }
    

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "filter_contacts",
        "description": "This tool filters a contact list based on specified criteria, and can only be used when a contact list has already been obtained.",
        "parameters": {
            "type": "object",
            "properties": {
                "group_filter": {
                    "type": "string",
                    "description": "Filter by group name (e.g., 'Family', 'Work Colleagues', 'College Friends', 'Book Lovers')"
                },
                "contact_filter": {
                    "type": "string", 
                    "description": "Filter by individual contact information (name, email, department, etc.)"
                }
            },
            "required": ["group_filter"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="filter_contacts",
        function=filter_contacts,
        schema=TOOL_SCHEMA,
        description="Tool function for filter_contacts"
    )

# Auto-register when module is imported
register_tool()
