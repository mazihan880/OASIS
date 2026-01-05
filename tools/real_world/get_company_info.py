#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get Company Info Tool
Retrieves comprehensive company information including business details, contact info, and financial data
Simulates real-world company information lookup with realistic data
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
import difflib

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
    # Try relative import first
    from ..resource.get_company_info_data import TASK_DATA
except ImportError:
    try:
        # Try absolute import as fallback
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resource_dir = os.path.join(current_dir, '..', 'resource')
        sys.path.insert(0, resource_dir)
        from get_company_info_data import TASK_DATA
    except ImportError:
        # Set empty data if all imports fail
        TASK_DATA = {}

# Set default values
    COMPANY_PATTERNS = {
        'inc': ['inc.', 'incorporated', 'corporation', 'corp', 'corp.'],
        'ltd': ['ltd.', 'limited', 'llc'],
        'company': ['company', 'co.', 'co'],
    }
    DEFAULT_COMPANY_RESULT = {
        "status": "success",
        "info": {
            "company_name": "Company search completed",
            "message": "Company information retrieval completed successfully"
        }
    }

def normalize_company_name(company_name: str) -> str:
    """
    Normalize company name for better matching
    
    Args:
        company_name: Raw company name input
        
    Returns:
        Normalized company name string
    """
    if not company_name:
        return ""
    
    # Convert to lowercase and remove extra whitespace
    normalized = company_name.lower().strip()
    
    # Remove common punctuation
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    
    # Normalize common company suffixes
    for pattern, replacements in COMPANY_PATTERNS.items():
        for replacement in replacements:
            normalized = re.sub(rf'\b{re.escape(replacement)}\b', pattern, normalized)
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def company_names_match(query_name: str, task_name: str, threshold: float = 0.6) -> bool:
    """
    Check if two company names match using fuzzy matching
    
    Args:
        query_name: Company name from query
        task_name: Company name from task data
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        True if names match above threshold
    """
    if not query_name or not task_name:
        return False
    
    # Normalize both names
    norm_query = normalize_company_name(query_name)
    norm_task = normalize_company_name(task_name)
    
    # Exact match after normalization
    if norm_query == norm_task:
        return True
    
    # Check if one is contained in the other
    if norm_query in norm_task or norm_task in norm_query:
        return True
    
    # Fuzzy matching using difflib
    similarity = difflib.SequenceMatcher(None, norm_query, norm_task).ratio()
    return similarity >= threshold

def calculate_company_match_score(query: str, task_queries: List[str]) -> float:
    """
    Calculate match score between query and task queries
    
    Args:
        query: User's company search query
        task_queries: List of queries from task data
        
    Returns:
        Match score (0.0 to 1.0)
    """
    if not query or not task_queries:
        return 0.0
    
    max_score = 0.0
    
    for task_query in task_queries:
        if company_names_match(query, task_query):
            max_score = max(max_score, 1.0)
        else:
            # Calculate similarity score
            norm_query = normalize_company_name(query)
            norm_task = normalize_company_name(task_query)
            
            if norm_query and norm_task:
                similarity = difflib.SequenceMatcher(None, norm_query, norm_task).ratio()
                max_score = max(max_score, similarity)
    
    return max_score

def get_company_info(*args, **kwargs) -> Dict[str, Any]:
    """
    Retrieve comprehensive company information
    
    Args:
        company_name: Name of the company to look up
        
    Returns:
        Dictionary containing company information and metadata
    """
    try:
        # Extract company_name from args or kwargs
        if args:
            company_name = args[0]
        elif 'company_name' in kwargs:
            company_name = kwargs['company_name']
        else:
            return {
                "result": {
                    "status": "error",
                    "message": "Company name parameter is required",
                    "error_code": "MISSING_PARAMETER"
                }
            }
        
        if not company_name or not isinstance(company_name, str):
            return {
                "result": {
                    "status": "error",
                    "message": "Company name is required and must be a string",
                    "error_code": "INVALID_INPUT"
                }
            }
        
        company_name = company_name.strip()
        if not company_name:
            return {
                "result": {
                    "status": "error", 
                    "message": "Company name cannot be empty",
                    "error_code": "EMPTY_INPUT"
                }
            }
        
        # Priority 1: Check if task context is active and has data
        if task_context.is_task_active():
            current_task_id = task_context.get_current_task_id()
            if current_task_id and current_task_id in TASK_DATA:
                task_data = TASK_DATA[current_task_id]
                
                # For multi-call tasks, find the best matching call within the task
                if 'calls' in task_data and isinstance(task_data['calls'], list) and len(task_data['calls']) > 0:
                    best_call_index = None
                    best_score = -1
                    
                    # Build query string from current parameters
                    current_query = company_name.lower()
                    
                    for i, call_data in enumerate(task_data['calls']):
                        # Get queries from call data
                        call_queries = call_data.get('queries', [])
                        call_best_score = 0.0
                        
                        for query in call_queries:
                            if query:
                                from difflib import SequenceMatcher
                                similarity = SequenceMatcher(None, current_query, query.lower()).ratio()
                                call_best_score = max(call_best_score, similarity)
                        
                        if call_best_score > best_score:
                            best_score = call_best_score
                            best_call_index = i
                    
                    # Use best match or fallback to first call if no good match
                    if best_call_index is None and task_data['calls']:
                        best_call_index = 0
                    
                    if best_call_index is not None:
                        call_data = task_data['calls'][best_call_index]
                        result = call_data.get('result', {}).copy()
                        return {
                            'result': result,
                        }
                else:
                    # Single call task - use task-level result directly
                    if task_data and 'result' in task_data:
                        result = task_data['result'].copy()
                        return {
                            'result': result,
                        }
        
        # Priority 2: Fallback to intelligent matching
        task_id, task_data, call_index = find_best_matching_task(company_name)
        
        if task_data and 'result' in task_data:
            result = task_data["result"].copy() if isinstance(task_data["result"], dict) else {"info": task_data["result"]}
        else:
            result = DEFAULT_COMPANY_RESULT.copy()
        
        return {
            'result': result,
        }
            
    except Exception as e:
        return {
            "result": {
                "status": "error",
                "message": f"Failed to retrieve company information: {str(e)}",
                "error_code": "COMPANY_INFO_ERROR"
            }
        }

def calculate_call_similarity(company_name: str, call_data: Dict[str, Any]) -> float:
    """
    Calculate similarity score between input and a specific call
    """
    score = 0.0
    
    # Check company_name parameter
    if company_name and 'company_name' in call_data:
        if company_names_match(company_name, call_data['company_name']):
            score += 30
    
    return score

def find_best_matching_task(company_name: str, call_index: int = None) -> tuple:
    """
    Find the best matching task for the given company name
    
    Args:
        company_name: Company name to search for
        call_index: Specific call index to match (optional)
        
    Returns:
        Tuple of (task_id, task_data, call_index) for calls structure or (task_id, task_data, None) for legacy
    """
    best_match = None
    best_score = 0.0
    best_task_id = None
    best_call_index = None
    
    for task_id, task_data in TASK_DATA.items():
        # Handle calls structure
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            for idx, call_data in enumerate(task_data['calls']):
                # If specific call_index is requested, only check that call
                if call_index is not None and idx != call_index:
                    continue
                
                call_sim = calculate_call_similarity(company_name, call_data)
                
                # Process queries in call_data
                queries = call_data.get('queries', [])
                if queries:
                    score = calculate_company_match_score(company_name, queries)
                    
                    # Add call similarity bonus
                    final_score = score + (call_sim * 0.1)
                    
                    if final_score > best_score:
                        best_score = final_score
                        best_match = call_data
                        best_task_id = task_id
                        best_call_index = idx
        
        # Handle legacy structure (no calls)
        else:
            if "queries" in task_data and task_data["queries"]:
                score = calculate_company_match_score(company_name, task_data["queries"])
                
                if score > best_score:
                    best_score = score
                    best_match = task_data
                    best_task_id = task_id
                    best_call_index = None
    
    # Return match only if score is above threshold
    if best_match and best_score >= 0.3:
        # For calls structure, return the call data with result
        if best_call_index is not None:
            result_data = {'result': best_match.get('result', best_match)}
            return (best_task_id, result_data, best_call_index)
        
        # For legacy structure, return the task data
        return (best_task_id, best_match, None)
    
    return (None, None, None)

# Tool schema for integration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_company_info",
        "description": "Retrieve comprehensive company information including business details, contact information, financial data, and corporate structure. Supports lookup by company name with fuzzy matching.",
        "parameters": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "Name of the company to look up. Can be partial name or include common variations (e.g., 'Apple Inc', 'Apple', 'Microsoft Corporation', 'Microsoft Corp')"
                }
            },
            "required": ["company_name"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="get_company_info",
        function=get_company_info,
        schema=TOOL_SCHEMA,
        description="Tool function for get_company_info"
    )

if __name__ == "__main__":
    # Test the tool with some examples
    test_companies = [
        "The Italian Homemade Company",
        "Eon Games", 
        "Apple Inc",
        "Microsoft",
        "Global Trust Bank",
        "Nonexistent Company"
    ]
    
    print("=" * 50)
    
    for company in test_companies:
        result = get_company_info(company)
        print(f"tasks ID: {result.get('task_id', 'None')}")
        
        if result.get('status') == 'success':
            if 'company_name' in result:
                print(f"Company: {result['company_name']}")
            elif 'info' in result and isinstance(result['info'], dict) and 'company_name' in result['info']:
                print(f"Company: {result['info']['company_name']}")
        print("-" * 30)

# Auto-register when module is imported
register_tool()
