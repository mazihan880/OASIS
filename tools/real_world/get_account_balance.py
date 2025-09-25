#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_account_balance tool implementation - tasks-Aware Version
Retrieve account balance information
"""

import json
import random
import re
from typing import Dict, Any, Optional, List, Union
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
    from ..resource.get_account_balance_data import TASK_DATA
except ImportError:
    TASK_DATA = {}

def get_account_balance(*args, **kwargs) -> Dict[str, Any]:
    """
    Retrieve account balance information
    
    Args:
        *args: Positional arguments (account_id, account_type, etc.)
        **kwargs: Keyword arguments (account_id, account_type, etc.)
    
    Returns:
        Dict containing the account balance response
    """
    
    try:
        # Extract parameters
        account_id = None
        account_type = None
        currency = None
        
        # Handle positional arguments
        if len(args) >= 1:
            account_id = str(args[0])
        if len(args) >= 2:
            account_type = str(args[1])
        if len(args) >= 3:
            currency = str(args[2])
        
        # Handle keyword arguments
        if 'account_id' in kwargs:
            account_id = str(kwargs['account_id'])
        if 'account_type' in kwargs:
            account_type = str(kwargs['account_type'])
        if 'currency' in kwargs:
            currency = str(kwargs['currency'])
        
        # Priority 1: Use task context data if available
        if task_context.is_task_active():
            current_task_id = task_context.get_current_task_id()
            if current_task_id and current_task_id in TASK_DATA:
                task_data = TASK_DATA[current_task_id]
                
                # For multi-call tasks, find the best matching call within the task
                if 'calls' in task_data and isinstance(task_data['calls'], list) and len(task_data['calls']) > 0:
                    best_call_index = None
                    best_score = -1
                    
                    # Build query string from current parameters
                    query_parts = []
                    if account_id:
                        query_parts.append(str(account_id).lower())
                    if account_type:
                        query_parts.append(str(account_type).lower())
                    if currency:
                        query_parts.append(str(currency).lower())
                    current_query = " ".join(query_parts)
                    
                    for i, call_data in enumerate(task_data['calls']):
                        # Get queries from call data
                        call_queries = call_data.get('queries', [])
                        call_best_score = 0.0
                        
                        for query in call_queries:
                            if query:
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
                        
                        # Add account details to response
                        if account_id:
                            result['account_id'] = account_id
                        if account_type:
                            result['account_type'] = account_type
                        if currency:
                            result['currency'] = currency
                        if 'transaction_id' not in result:
                            result['transaction_id'] = f"txn_{random.randint(100000, 999999)}"
                        
                        # Add debug metadata
                            'method': 'task_context',
                            'matched_task_id': current_task_id,
                            'call_index': best_call_index,
                            'best_score': best_score,
                            'task_active': True,
                            'matched_task': True,
                            'multi_call': True
                        }
                        return {
                            'result': result,
                        }
                else:
                    # Single call task - use task-level result directly
                    result = task_data.get('result', {}).copy()
                    
                    # Add account details to response
                    if account_id:
                        result['account_id'] = account_id
                    if account_type:
                        result['account_type'] = account_type
                    if currency:
                        result['currency'] = currency
                    if 'transaction_id' not in result:
                        result['transaction_id'] = f"txn_{random.randint(100000, 999999)}"
                    
                    # Add debug metadata
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': None,
                        'task_active': True,
                        'matched_task': True,
                        'multi_call': False
                    }
                    return {
                        'result': result,
                    }
        
        # Priority 2: Fallback to intelligent matching
        # Get balance result based on parameters
        result = get_balance_result(account_id, account_type, currency)
        
        # Add metadata to response
        if account_id:
            result['account_id'] = account_id
        if account_type:
            result['account_type'] = account_type
        if currency:
            result['currency'] = currency
        if 'transaction_id' not in result:
            result['transaction_id'] = f"txn_{random.randint(100000, 999999)}"
        
        # Add debug metadata
            'method': 'fallback',
            'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            'matched_task': False,
            'multi_call': False,
            'matched_task_id': None
        }
        
        return {
            'result': result,
        }
            
    except Exception as e:
        return {
            "result": {
                "status": "error",
                "message": f"Failed to retrieve account balance: {str(e)}",
                "tool": "get_account_balance"
            },
                "method": "exception_fallback",
                "error": str(e),
                "task_active": False,
                "matched_task": False,
                "multi_call": False,
                "matched_task_id": None
            }
        }

def get_balance_result(account_id: str = None, account_type: str = None, currency: str = None) -> Dict[str, Any]:
    """
    Get balance result based on parameters
    
    Args:
        account_id: Account identifier
        account_type: Type of account (checking, savings, etc.)
        currency: Currency code
    
    Returns:
        Dict containing the balance response
    """
    
    if not TASK_DATA:
        return generate_fallback_response(account_id, account_type, currency)
    
    # Try to find matching task data
    task_id, task_data, call_index = find_best_match(account_id, account_type, currency)
    
    if task_data:
        # Handle calls structure
        if 'calls' in task_data and call_index is not None:
            call_data = task_data['calls'][call_index]
            result = call_data['result'].copy()
        else:
            # Legacy structure
            result = task_data['result'].copy()
        
        # Ensure balance is in the correct format
        if 'balance' in result and isinstance(result['balance'], (int, float)):
            # Convert simple balance number to structured format
            balance_amount = result['balance']
            result['balance'] = {
                "amount": balance_amount,
                "currency": result.get('currency', 'USD'),
                "available_balance": balance_amount
            }
        
        result['scenario'] = task_data.get('scenario', 'unknown')
        result['example_number'] = task_data.get('example_number', 0)
        
        # Add debug metadata
            'method': 'intelligent_matching',
            'matched_task_id': task_id,
            'call_index': call_index,
            'task_active': task_context.is_task_active()
        }
        return result
    
    # Return fallback response
    fallback_result = generate_fallback_response(account_id, account_type, currency)
        'method': 'fallback',
        'task_active': task_context.is_task_active()
    }
    return fallback_result

def calculate_call_similarity(account_id: str, account_type: str, currency: str, call_data: Dict[str, Any]) -> float:
    """
    Calculate similarity score between input and a specific call
    """
    score = 0.0
    
    # Check account parameters
    if account_id and 'account_id' in call_data:
        if call_data['account_id'].lower() == account_id.lower():
            score += 25
    
    if account_type and 'account_type' in call_data:
        if call_data['account_type'].lower() == account_type.lower():
            score += 20
    
    if currency and 'currency' in call_data:
        if call_data['currency'].lower() == currency.lower():
            score += 15
    
    return score

def find_best_match(account_id: str = None, account_type: str = None, currency: str = None, call_index: int = None) -> tuple:
    """
    Find the best matching task data based on enhanced multi-dimensional similarity
    
    Args:
        account_id: Account identifier or number
        account_type: Type of account
        currency: Currency code
        call_index: Specific call index to match (optional)
    
    Returns:
        Tuple of (task_id, task_data, call_index) for calls structure or (task_id, task_data, None) for legacy
    """
    
    if not TASK_DATA:
        return (None, None, None)
    
    best_match = None
    best_score = 0.0
    best_call_index = None
    # When task context is active, remove threshold to always return best match
    min_threshold = 0.0 if (hasattr(task_context, 'is_task_active') and task_context.is_task_active()) else 0.35
    
    # Create search query from parameters
    search_parts = []
    if account_id:
        search_parts.append(account_id.lower().strip())
    if account_type:
        search_parts.append(account_type.lower().strip())
    if currency:
        search_parts.append(currency.lower().strip())
    
    search_query = " ".join(search_parts)
    
    # Track all potential matches for conflict resolution
    potential_matches = []
    
    for task_id, task_data in TASK_DATA.items():
        # Handle calls structure
        if 'calls' in task_data:
            for call_idx, call_data in enumerate(task_data['calls']):
                # If specific call_index is requested, only check that call
                if call_index is not None and call_idx != call_index:
                    continue
                
                # Calculate call-specific similarity
                call_sim = calculate_call_similarity(account_id or "", account_type or "", currency or "", call_data)
                
                # Process queries for this call
                queries = call_data.get('queries', [])
                for task_query in queries:
                    if not task_query:
                        continue
                        
                    normalized_task_query = task_query.lower().strip()
                    
                    # Calculate multiple similarity metrics
                    sequence_sim = SequenceMatcher(None, search_query, normalized_task_query).ratio()
                    word_overlap_sim = calculate_word_overlap_similarity(search_query, normalized_task_query)
                    substring_sim = calculate_substring_similarity(search_query, normalized_task_query)
                    keyword_sim = calculate_keyword_similarity(search_query, normalized_task_query)
                    fuzzy_sim = calculate_fuzzy_similarity(search_query, normalized_task_query)
                    
                    similarity_scores = [sequence_sim, word_overlap_sim, substring_sim, keyword_sim, fuzzy_sim]
                    weights = [0.25, 0.25, 0.2, 0.15, 0.15]
                    final_score = sum(score * weight for score, weight in zip(similarity_scores, weights))
                    
                    # Add call-specific similarity bonus
                    final_score += call_sim * 0.01
                    
                    if final_score > best_score:
                        best_score = final_score
                        best_match = (task_id, task_data)
                        best_call_index = call_idx
        else:
            # Legacy structure support
            queries = task_data.get('queries', [])
            for task_query in queries:
                if not task_query:
                    continue
                    
                normalized_task_query = task_query.lower().strip()
                
                # Calculate multiple similarity metrics
                sequence_sim = SequenceMatcher(None, search_query, normalized_task_query).ratio()
                word_overlap_sim = calculate_word_overlap_similarity(search_query, normalized_task_query)
                substring_sim = calculate_substring_similarity(search_query, normalized_task_query)
                keyword_sim = calculate_keyword_similarity(search_query, normalized_task_query)
                fuzzy_sim = calculate_fuzzy_similarity(search_query, normalized_task_query)
                
                similarity_scores = [sequence_sim, word_overlap_sim, substring_sim, keyword_sim, fuzzy_sim]
                weights = [0.25, 0.25, 0.2, 0.15, 0.15]
                final_score = sum(score * weight for score, weight in zip(similarity_scores, weights))
                
                if final_score > best_score:
                    best_score = final_score
                    best_match = (task_id, task_data)
                    best_call_index = None
        
    # Return the best match found
    if best_match and best_score >= min_threshold:
        task_id, task_data = best_match
        return (task_id, task_data, best_call_index)
    
    # Return default balance if available and no match found
    if 'default_balance_retrieved' in TASK_DATA:
        return ('default_balance_retrieved', TASK_DATA['default_balance_retrieved'], None)
    
    # Return any available task data as fallback
    if TASK_DATA:
        first_task_id = list(TASK_DATA.keys())[0]
        return (first_task_id, TASK_DATA[first_task_id], None)
    
    return (None, None, None)

def calculate_word_overlap_similarity(query1: str, query2: str) -> float:
    """Calculate word overlap similarity between two queries"""
    words1 = set(query1.split())
    words2 = set(query2.split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    return intersection / union if union > 0 else 0.0

def calculate_substring_similarity(query1: str, query2: str) -> float:
    """Calculate substring similarity between two queries"""
    if query1 in query2 or query2 in query1:
        return min(len(query1), len(query2)) / max(len(query1), len(query2))
    return 0.0

def calculate_keyword_similarity(query1: str, query2: str) -> float:
    """Calculate keyword-based similarity"""
    keywords = ['checking', 'savings', 'credit', 'investment', 'balance', 'account', 'bank', 'usd', 'eur', 'gbp']
    query1_keywords = [kw for kw in keywords if kw in query1.lower()]
    query2_keywords = [kw for kw in keywords if kw in query2.lower()]
    
    if not query1_keywords and not query2_keywords:
        return 0.0
    
    common_keywords = set(query1_keywords).intersection(set(query2_keywords))
    total_keywords = set(query1_keywords).union(set(query2_keywords))
    
    return len(common_keywords) / len(total_keywords) if total_keywords else 0.0

def calculate_fuzzy_similarity(query1: str, query2: str) -> float:
    """Calculate fuzzy similarity using character-level matching"""
    if not query1 or not query2:
        return 0.0
    
    # Simple character-based fuzzy matching
    common_chars = 0
    for char in query1:
        if char in query2:
            common_chars += 1
    
    return common_chars / max(len(query1), len(query2))

def generate_fallback_response(account_id: str = None, account_type: str = None, currency: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific match is found
    
    Args:
        account_id: Account identifier
        account_type: Type of account
        currency: Currency code
    
    Returns:
        Dict containing fallback balance response
    """
    
    # Default currency
    if not currency:
        currency = "USD"
    
    response = {
        "status": "success",
        "message": "Account balance retrieved successfully",
        "transaction_id": f"txn_{random.randint(100000, 999999)}",
        "timestamp": "2025-01-21T10:00:00Z",
        "tool": "get_account_balance",
        "balance": {
            "amount": round(random.uniform(100.0, 10000.0), 2),
            "currency": currency,
            "available_balance": round(random.uniform(100.0, 10000.0), 2)
        }
    }
    
    # Generate contextual responses based on account type
    if account_type:
        account_type_lower = account_type.lower()
        
        if 'checking' in account_type_lower:
            response['account_type'] = 'checking'
            response['balance']['amount'] = round(random.uniform(500.0, 5000.0), 2)
            
        elif 'savings' in account_type_lower:
            response['account_type'] = 'savings'
            response['balance']['amount'] = round(random.uniform(1000.0, 20000.0), 2)
            response['balance']['interest_rate'] = "2.5%"
            
        elif 'credit' in account_type_lower:
            response['account_type'] = 'credit'
            response['balance']['amount'] = round(random.uniform(-1000.0, 0.0), 2)
            response['balance']['credit_limit'] = round(random.uniform(5000.0, 25000.0), 2)
            response['balance']['available_credit'] = response['balance']['credit_limit'] + response['balance']['amount']
            
        elif 'investment' in account_type_lower:
            response['account_type'] = 'investment'
            response['balance']['amount'] = round(random.uniform(5000.0, 50000.0), 2)
            response['balance']['market_value'] = response['balance']['amount']
            response['balance']['unrealized_gain_loss'] = round(random.uniform(-500.0, 1000.0), 2)
    
    # Add account ID if provided
    if account_id:
        response['account_id'] = account_id
    else:
        response['account_id'] = f"ACC_{random.randint(100000, 999999)}"
    
    return response

# Tool registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_account_balance",
        "description": "Retrieve account balance information",
        "parameters": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "Account identifier or number"
                },
                "account_type": {
                    "type": "string",
                    "description": "Type of account (checking, savings, credit, investment, etc.)"
                },
                "currency": {
                    "type": "string",
                    "description": "Currency code (USD, EUR, GBP, etc.)"
                }
            },
            "required": []
        }
    }
}

def register_tool(registry=None):
    """Register this tool with the tool registry"""
    if registry is not None:
        registry["get_account_balance"] = get_account_balance
    else:
        # Auto-register with global registry
        from ..tool_registry import registry as global_registry
        global_registry.register(
            name="get_account_balance",
            function=get_account_balance,
            schema=TOOL_SCHEMA,
            description="Retrieve account balance information"
        )
    return {
        "function": get_account_balance,
        "schema": TOOL_SCHEMA
    }


# Auto-register when module is imported
register_tool()