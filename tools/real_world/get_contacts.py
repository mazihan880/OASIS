#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get Contacts Tool - tasks-Aware Version
Retrieve contact list associated with account
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
    from ..resource.get_contacts_data import TASK_DATA, DEFAULT_CONTACT_RESULT
except ImportError:
    TASK_DATA = {}
    DEFAULT_CONTACT_RESULT = {"status": "error", "message": "Resource data not available"}

def get_contacts(*args, **kwargs) -> Dict[str, Any]:
    """
    Retrieve contact list associated with account with task context support
    
    Args:
        *args: Positional arguments (source, etc.)
        **kwargs: Keyword arguments (source, etc.)
    
    Returns:
        Dict containing the contact retrieval response
    """
    
    try:
        # Extract source parameter
        source = None
        
        # Handle positional arguments
        if len(args) >= 1:
            source = str(args[0])
        
        # Handle keyword arguments
        if 'source' in kwargs:
            source = str(kwargs['source'])
        
        # Check for task context first (priority)
        current_task_id = task_context.get_current_task_id()
        if current_task_id and task_context.is_task_active() and current_task_id in TASK_DATA:
            task_data = TASK_DATA[current_task_id]
            
            # For multi-call tasks, find the best matching call within the task
            if 'calls' in task_data and isinstance(task_data['calls'], list) and len(task_data['calls']) > 0:
                best_call_index = None
                best_score = -1
                
                def build_query_string(call_data):
                    """Build a query string from call data for similarity comparison"""
                    parts = []
                    if 'source' in call_data:
                        parts.append(str(call_data['source']))
                    if 'args' in call_data and 'source' in call_data['args']:
                        parts.append(str(call_data['args']['source']))
                    return ' '.join(parts).lower()
                
                for i, call_data in enumerate(task_data['calls']):
                    call_query = build_query_string(call_data)
                    
                    # Calculate similarity using SequenceMatcher
                    source_str = source.lower() if source else ''
                    similarity = SequenceMatcher(None, source_str, call_query).ratio()
                    
                    if similarity > best_score:
                        best_score = similarity
                        best_call_index = i
                
                # If no match found, fallback to first call
                if best_call_index is None:
                    best_call_index = 0
                    best_score = 0.0
                
                call_data = task_data['calls'][best_call_index]
                result = call_data.get('result', DEFAULT_CONTACT_RESULT).copy()
                
                # Add contact details to response
                if source:
                    result['source'] = source
                if 'contact_id' not in result:
                    result['contact_id'] = f"contact_{random.randint(100000, 999999)}"
                
                return {
                    "result": result,
                }
            else:
                # Single call task - use task-level result directly
                result = task_data.get('result', DEFAULT_CONTACT_RESULT).copy()
                
                # Add contact details to response
                if source:
                    result['source'] = source
                if 'contact_id' not in result:
                    result['contact_id'] = f"contact_{random.randint(100000, 999999)}"
                
                return {
                    "result": result,
                }
        
        # Fallback to intelligent matching
        task_id, task_data, call_index = find_best_matching_task(source)
        
        if task_data and 'result' in task_data:
            result = task_data['result'].copy()
        else:
            result = get_contacts_by_source(source)
        
        # Add contact details to response
        if source:
            result['source'] = source
        if 'contact_id' not in result:
            result['contact_id'] = f"contact_{random.randint(100000, 999999)}"
        
        return {
            "result": result,
        }
            
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Failed to retrieve contacts: {str(e)}",
            "tool": "get_contacts"
        }
        return {
            "result": result,
        }

def calculate_call_similarity(source: str, call_data: Dict[str, Any]) -> float:
    """
    Calculate similarity score between input and a specific call
    """
    score = 0.0
    
    # Check source parameter
    if source and 'source' in call_data:
        if call_data['source'].lower() == source.lower():
            score += 30
    
    return score

def find_best_matching_task(source: str = None, call_index: int = None) -> tuple:
    """
    Find the best matching task for the given source
    
    Args:
        source: Contact source to search for
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
    
    source_lower = source.lower().strip() if source else ""
    
    for task_id, task_data in TASK_DATA.items():
        # Handle calls structure
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            for idx, call_data in enumerate(task_data['calls']):
                # If specific call_index is requested, only check that call
                if call_index is not None and idx != call_index:
                    continue
                
                call_sim = calculate_call_similarity(source, call_data)
                
                # Process queries in call_data
                queries = call_data.get('queries', [])
                for query in queries:
                    query_lower = query.lower().strip()
                    
                    # Calculate similarity score
                    similarity = SequenceMatcher(None, source_lower, query_lower).ratio()
                    
                    # Boost score for exact matches
                    if source_lower == query_lower:
                        similarity += 1.0
                    
                    # Boost score for containment
                    if source_lower in query_lower or query_lower in source_lower:
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
                similarity = SequenceMatcher(None, source_lower, query_lower).ratio()
                
                # Boost score for exact matches
                if source_lower == query_lower:
                    similarity += 1.0
                
                # Boost score for containment
                if source_lower in query_lower or query_lower in source_lower:
                    similarity += 0.5
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = task_data
                    best_task_id = task_id
                    best_call_index = None
    
    # Use threshold for matching - remove threshold when task context is active
    threshold = 0.0 if (hasattr(task_context, 'is_task_active') and task_context.is_task_active()) else 0.3
    if best_score < threshold:
        return (None, {'result': DEFAULT_CONTACT_RESULT}, None)
    
    # For calls structure, return the call data with result
    if best_call_index is not None:
        result_data = {'result': best_match.get('result', best_match)}
        return (best_task_id, result_data, best_call_index)
    
    # For legacy structure, return the task data
    return (best_task_id, best_match, None)

def get_contacts_by_source(source: str = None) -> Dict[str, Any]:
    """
    Get contact data based on source parameter
    
    Args:
        source: Contact source (e.g., "Google", "LinkedIn", "corporate", etc.)
    
    Returns:
        Dict containing the contact retrieval response
    """
    
    # Import the unified contact data
    try:
        from ..resource.get_contacts_data import MY_CONTACTS_DATA, SPECIAL_SOURCE_DATA
    except ImportError:
        return DEFAULT_CONTACT_RESULT
    
    if not source:
        # Default: return my contacts
        return MY_CONTACTS_DATA.copy()
    
    source_lower = source.lower().strip()
    
    # Check for special sources first
    if source_lower in SPECIAL_SOURCE_DATA:
        return SPECIAL_SOURCE_DATA[source_lower].copy()
    
    # For all other sources (Google, Outlook, iCloud, Gmail, etc.), return my contacts
    # This allows multiple tasks to share the same contact list
    result = MY_CONTACTS_DATA.copy()
    result['source'] = source
    return result

def generate_fallback_response(source: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific match is found
    
    Args:
        source: Contact source
    
    Returns:
        Dict containing fallback contact response
    """
    
    response = {
        "status": "success",
        "message": "Contacts retrieved successfully",
        "contact_id": f"contact_{random.randint(100000, 999999)}",
        "timestamp": "2025-01-21T10:00:00Z",
        "tool": "get_contacts",
        "contacts": [
            {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "groups": ["Default"]
            },
            {
                "name": "Jane Smith", 
                "email": "jane.smith@example.com",
                "groups": ["Default"]
            }
        ]
    }
    
    if source:
        response['source'] = source
    
    # Generate contextual responses based on content
    if source:
        if 'google' in source.lower():
            response['message'] = "Google contacts retrieved successfully."
        elif 'outlook' in source.lower():
            response['message'] = "Outlook contacts retrieved successfully."
        elif 'icloud' in source.lower():
            response['message'] = "iCloud contacts retrieved successfully."
    
    return response

# Tool registration (following web_search pattern)
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_contacts",
        "description": "Retrieve a contact list. Can fetch from the user's own integrated accounts (like Google Contacts) or from a user's public connections on a specified social media platform.",
        "parameters": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "Optional. The social media platform from which to retrieve public contacts or connections. Supported platforms: 'LinkedIn', 'X', 'Facebook'. If this is provided, 'username' is also required."
                },
                "username": {
                    "type": "string",
                    "description": "Optional. The username of the target account on the specified platform. Required if 'platform' is used."
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
        name="get_contacts",
        function=get_contacts,
        schema=TOOL_SCHEMA,
        description="Tool function for get_contacts"
    )

# Auto-register when module is imported
register_tool()
