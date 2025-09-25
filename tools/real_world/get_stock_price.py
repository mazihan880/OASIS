#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_stock_price tool implementation
Get current market price for stocks
"""

import json
import random
import re
import time
from typing import Dict, Any, Optional
from difflib import SequenceMatcher

# Global call counter to track calls per task_id
_call_counter = {}

def get_and_increment_call_count(task_id: str) -> int:
    """
    Get current call count for a task_id and increment it
    
    Args:
        task_id: The task identifier
    
    Returns:
        Current call count (0-based index)
    """
    if task_id not in _call_counter:
        _call_counter[task_id] = 0
    else:
        _call_counter[task_id] += 1
    return _call_counter[task_id]

def reset_call_count(task_id: str = None):
    """
    Reset call count for a specific task_id or all tasks
    
    Args:
        task_id: tasks ID to reset, or None to reset all
    """
    if task_id is None:
        _call_counter.clear()
    elif task_id in _call_counter:
        del _call_counter[task_id]

# Import task context manager
try:
    from ...evaluation.task_context import task_context
except ImportError:
    try:
        from AgentSafe.evaluation.task_context import task_context
    except ImportError:
        # Create a dummy task_context for fallback
        class DummytasksContext:
            def is_task_active(self): return False
            def get_current_task_id(self): return None
            def get_task_data(self, task_id): return None
        task_context = DummytasksContext()

# Import resource data
try:
    from ..resource.get_stock_price_data import TASK_DATA, DEFAULT_STOCK_RESULT
except ImportError:
    TASK_DATA = {}
    DEFAULT_STOCK_RESULT = {"status": "success", "message": "Stock price retrieved successfully", "price": 100.0}

def get_stock_price(*args, **kwargs) -> Dict[str, Any]:
    """
    Get current market price for stocks
    
    Args:
        *args: Positional arguments (symbol, ticker, etc.)
        **kwargs: Keyword arguments (symbol, ticker, etc.)
    
    Returns:
        Dict containing the stock price information
    """
    
    try:
        # Extract stock parameters
        symbol = None
        ticker = None
        company_name = None
        include_details = False
        
        # Handle positional arguments
        if len(args) >= 1:
            symbol = str(args[0]).strip()
        
        # Handle keyword arguments
        symbol = kwargs.get('symbol', symbol)
        ticker = kwargs.get('ticker', ticker)
        company_name = kwargs.get('company_name', company_name)
        include_details = kwargs.get('include_details', include_details)
        
        # Use symbol, ticker, or company_name as primary identifier
        query_symbol = symbol or ticker or company_name
        
        if not query_symbol:
            return {
                "status": "error",
                "message": "No stock symbol, ticker, or company name provided",
                "error_code": "MISSING_SYMBOL"
            }
        
        # Normalize the query symbol
        normalized_symbol = normalize_symbol(query_symbol)
        
        # Priority 1: Check if task context is active and has data
        if task_context.is_task_active():
            current_task_id = task_context.get_current_task_id()
            if current_task_id and current_task_id in TASK_DATA:
                task_data = TASK_DATA[current_task_id]
                
                # For multi-call tasks, use call count to determine which call to return
                if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                    # Get current call count and increment it
                    call_index = get_and_increment_call_count(current_task_id)
                    
                    # Ensure call_index is within bounds, cycle if necessary
                    total_calls = len(task_data['calls'])
                    call_index = call_index % total_calls
                    
                    call_data = task_data['calls'][call_index]
                    result = call_data.get('result', DEFAULT_STOCK_RESULT).copy()
                        'method': 'task_context_count',
                        'matched_task_id': current_task_id,
                        'call_index': call_index,
                        'task_active': True,
                        'query_used': normalized_symbol,
                        'call_count': call_index + 1,  # 1-based for display
                        'total_calls': total_calls,
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
                    result = task_data.get('result', DEFAULT_STOCK_RESULT).copy()
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': None,
                        'task_active': True,
                        'query_used': normalized_symbol,
                        'task_id': current_task_id,
                        'scenario': task_data.get('scenario', 'unknown'),
                        'matched_task': True,
                        'multi_call': False
                    }
                    return {
                        'result': result,
                    }
        
        # Priority 2: Fallback to intelligent matching
        matching_task = find_best_matching_task(normalized_symbol)
        
        if matching_task:
            task_id, task_data, call_index = matching_task
            
            # Handle multi-call tasks with calls array
            if 'calls' in task_data and call_index is not None:
                call_data = task_data['calls'][call_index]
                result = call_data.get("result", DEFAULT_STOCK_RESULT).copy()
                    'method': 'similarity_match',
                    'matched_task_id': task_id,
                    'call_index': call_index,
                    'query_used': normalized_symbol,
                    'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                    'matched_task': True,
                    'multi_call': True
                }
            else:
                # Handle legacy single task structure
                result = task_data.get("result", DEFAULT_STOCK_RESULT).copy()
                    'method': 'similarity_match',
                    'matched_task_id': task_id,
                    'query_used': normalized_symbol,
                    'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                    'matched_task': True,
                    'multi_call': False
                }
            
            return {
                'result': result,
            }
        
        # If no specific task matches, return default response
        result = generate_fallback_response(normalized_symbol)
            'method': 'fallback',
            'query_used': normalized_symbol,
            'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            'matched_task': False,
            'multi_call': False,
            'matched_task_id': None
        }
        return {
            'result': result,
        }
        
    except Exception as e:
        # Ensure no errors are raised - return safe default
        result = {
            "status": "success",
            "message": "Stock price retrieved successfully",
            "symbol": str(symbol or ticker or company_name or "UNKNOWN"),
            "price": 100.0,
            "currency": "USD",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": "Default response - sandbox environment"
        }
            "method": "exception_fallback",
            "error": str(e),
            "task_active": False,
            "matched_task": False,
            "multi_call": False,
            "matched_task_id": None
        }
        return {
            'result': result,
        }

def find_best_matching_task(query_symbol: str) -> Optional[tuple]:
    """
    Find the best matching task for the given query symbol
    Supports both single tasks and multi-call tasks with calls array.
    
    Args:
        query_symbol: Normalized symbol to search for
    
    Returns:
        Tuple of (task_id, task_data, call_index) if found, None otherwise
        For single tasks, call_index is None
        For multi-call tasks, call_index indicates which call matched
    """
    
    if not TASK_DATA:
        return None
    
    best_match = None
    best_score = 0.0
    
    # Dynamic threshold based on task context
    if task_context.is_task_active():
        min_threshold = 0.0  # Always return best match when task is active
    else:
        min_threshold = 0.6  # Minimum threshold for matching
    
    for task_id, task_data in TASK_DATA.items():
        # Handle new calls array structure for multi-call tasks
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            for call_idx, call_data in enumerate(task_data['calls']):
                queries = call_data.get("queries", [])
                
                for query in queries:
                    # Handle wildcard matches
                    if query == "*":
                        if best_score < 0.5:  # Only use wildcard if no better match
                            best_match = (task_id, task_data, call_idx)
                            best_score = 0.5
                        continue
                    
                    # Normalize query for comparison
                    normalized_query = normalize_symbol(query)
                    
                    # Exact match gets highest priority
                    if normalized_query == query_symbol:
                        return (task_id, task_data, call_idx)
                    
                    # Calculate similarity score
                    similarity = SequenceMatcher(None, normalized_query, query_symbol).ratio()
                    
                    # Check if symbol is contained in query or vice versa
                    if query_symbol in normalized_query or normalized_query in query_symbol:
                        similarity = max(similarity, 0.8)
                    
                    # Update best match if this is better
                    if similarity > best_score and similarity > min_threshold:
                        best_match = (task_id, task_data, call_idx)
                        best_score = similarity
        else:
            # Handle legacy single task structure
            queries = task_data.get("queries", [])
            
            for query in queries:
                # Handle wildcard matches
                if query == "*":
                    if best_score < 0.5:  # Only use wildcard if no better match
                        best_match = (task_id, task_data, None)
                        best_score = 0.5
                    continue
                
                # Normalize query for comparison
                normalized_query = normalize_symbol(query)
                
                # Exact match gets highest priority
                if normalized_query == query_symbol:
                    return (task_id, task_data, None)
                
                # Calculate similarity score
                similarity = SequenceMatcher(None, normalized_query, query_symbol).ratio()
                
                # Check if symbol is contained in query or vice versa
                if query_symbol in normalized_query or normalized_query in query_symbol:
                    similarity = max(similarity, 0.8)
                
                # Update best match if this is better
                if similarity > best_score and similarity > min_threshold:
                    best_match = (task_id, task_data, None)
                    best_score = similarity
    
    return best_match

def normalize_symbol(symbol: str) -> str:
    """
    Normalize a stock symbol for consistent matching
    
    Args:
        symbol: Raw symbol string
    
    Returns:
        Normalized symbol string
    """
    if not symbol:
        return ""
    
    # Convert to uppercase and remove common prefixes/suffixes
    normalized = symbol.upper().strip()
    
    # Remove dollar sign prefix
    if normalized.startswith('$'):
        normalized = normalized[1:]
    
    # Remove common stock-related words
    stock_words = ['STOCK', 'PRICE', 'TICKER', 'QUOTE', 'INC', 'CORP', 'LTD', 'LLC']
    for word in stock_words:
        normalized = normalized.replace(word, '').strip()
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    return normalized

def generate_fallback_response(symbol: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific task matches
    
    Args:
        symbol: The queried symbol
    
    Returns:
        Default stock price response
    """
    
    # Use default result as base
    result = DEFAULT_STOCK_RESULT.copy()
    
    if symbol:
        result["symbol"] = symbol
        result["ticker_symbol"] = symbol
        
        # Generate a realistic-looking price based on symbol hash
        price_seed = hash(symbol) % 1000
        result["price"] = round(50.0 + (price_seed / 10.0), 2)
    else:
        result["price"] = 100.0
    
    result["currency"] = "USD"
    result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    result["note"] = "Default response - no specific task match found"
    
    return result

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_stock_price",
        "description": "Get current market price for stocks",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol or ticker (e.g., AAPL, GOOGL, TSLA)"
                },
                "ticker": {
                    "type": "string", 
                    "description": "Stock ticker symbol (alternative to symbol)"
                },
                "company_name": {
                    "type": "string",
                    "description": "Company name (e.g., Apple Inc., Tesla)"
                },
                "include_details": {
                    "type": "boolean",
                    "description": "Whether to include detailed market information (volume, market cap, etc.)",
                    "default": False
                }
            },
            "required": ["symbol"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="get_stock_price",
        function=get_stock_price,
        schema=TOOL_SCHEMA,
        description="Tool function for get_stock_price"
    )

# Auto-register when module is imported
register_tool()
