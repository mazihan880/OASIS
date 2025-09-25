#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_crypto_price tool implementation
Get current price of cryptocurrency
"""

import json
import random
import re
from typing import Dict, Any, Optional
from difflib import SequenceMatcher

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
    # Try relative import first
    from ..resource.get_crypto_price_data import TASK_DATA
except ImportError:
    try:
        # Try absolute import as fallback
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resource_dir = os.path.join(current_dir, '..', 'resource')
        sys.path.insert(0, resource_dir)
        from get_crypto_price_data import TASK_DATA
    except ImportError:
        # Set empty data if all imports fail
        TASK_DATA = {}

# Set default values
DEFAULT_CRYPTO_RESULT = {"status": "success", "message": "Cryptocurrency price query completed", "crypto_symbol": "BTC", "price": 68500.00, "currency": "USD"}
CRYPTO_ALIASES = {
    'btc': ['bitcoin', 'bitcoin price', 'btc price', 'btc usd', 'bitcoin usd'],
    'eth': ['ethereum', 'ethereum price', 'eth price', 'eth usd', 'ethereum usd'],
    'usdt': ['tether', 'tether price', 'usdt price', 'stablecoin_price'],
    'xlm': ['stellar', 'stellar lumens', 'xlm price'],
    'xmr': ['monero', 'monero price', 'privacy_coin']
}

def get_crypto_symbol_from_query(query):
    return "BTC"

def normalize_crypto_query(query):
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
    norm1 = normalize_crypto_query(query1)
    norm2 = normalize_crypto_query(query2)
    
    # Calculate sequence similarity
    return SequenceMatcher(None, norm1, norm2).ratio()

def is_crypto_query(query: str) -> bool:
    """
    Determine if a query is specifically asking for cryptocurrency prices
    
    Args:
        query: Query string to analyze
    
    Returns:
        True if query is crypto-related, False if it might be stock-related
    """
    if not query:
        return True  # Default to crypto if no context
    
    query_lower = query.lower()
    
    # Strong crypto indicators
    crypto_indicators = [
        'crypto', 'cryptocurrency', 'bitcoin', 'btc', 'ethereum', 'eth', 
        'altcoin', 'defi', 'blockchain', 'digital currency', 'virtual currency',
        'satoshi', 'wei', 'gwei', 'mining', 'wallet', 'exchange rate'
    ]
    
    # Strong stock indicators
    stock_indicators = [
        'stock', 'share', 'equity', 'nasdaq', 'nyse', 'dow jones', 'sp500',
        'market cap', 'dividend', 'earnings', 'quarterly', 'annual report',
        'ticker symbol', 'trading volume', 'pe ratio', 'market value'
    ]
    
    # Check for crypto indicators
    crypto_score = sum(1 for indicator in crypto_indicators if indicator in query_lower)
    
    # Check for stock indicators  
    stock_score = sum(1 for indicator in stock_indicators if indicator in query_lower)
    
    # If both present, prefer the one with higher score
    if crypto_score > 0 and stock_score > 0:
        return crypto_score >= stock_score
    
    # If only crypto indicators present
    if crypto_score > 0:
        return True
    
    # If only stock indicators present
    if stock_score > 0:
        return False
    
    # Check for known crypto symbols/names
    known_cryptos = ['btc', 'eth', 'usdt', 'bnb', 'ada', 'xrp', 'sol', 'dot', 'doge', 'avax']
    if any(crypto in query_lower for crypto in known_cryptos):
        return True
    
    # Check for known stock symbols (common ones that might be confused)
    known_stocks = ['aapl', 'googl', 'msft', 'tsla', 'amzn', 'nvda', 'meta', 'nflx']
    if any(stock in query_lower for stock in known_stocks):
        return False
    
    # Default to crypto for this tool
    return True

def calculate_crypto_priority(task_query: str, symbol: str = None) -> float:
    """
    Calculate priority score based on cryptocurrency symbol matching
    
    Args:
        task_query: The task query string to match against
        symbol: Cryptocurrency symbol
    
    Returns:
        Priority score (0.0 to 1.0)
    """
    score = 0.0
    
    if not task_query:
        return score
    
    # First check if this is actually a crypto query
    if not is_crypto_query(task_query):
        return 0.0  # Return 0 if this seems like a stock query
    
    query_lower = task_query.lower()
    
    # Check for cryptocurrency symbol matches
    if symbol:
        symbol_lower = symbol.lower()
        if symbol_lower in query_lower:
            score += 0.5
        
        # Check aliases
        if symbol_lower in CRYPTO_ALIASES:
            for alias in CRYPTO_ALIASES[symbol_lower]:
                if alias.lower() in query_lower:
                    score += 0.3
                    break
    
    # Check for general crypto terms
    crypto_terms = ['cryptocurrency', 'crypto', 'price', 'market', 'value', 'trading', 'exchange']
    for term in crypto_terms:
        if term in query_lower:
            score += 0.1
    
    return min(score, 1.0)

def get_crypto_price(*args, **kwargs) -> Dict[str, Any]:
    """
    Get current price of cryptocurrency
    
    Args:
        symbol (str, optional): Cryptocurrency symbol (e.g., 'BTC', 'ETH')
        query (str, optional): Query string for matching
    
    Returns:
        Dict containing cryptocurrency price information
    """
    
    try:
        # Handle both positional and keyword arguments
        if args:
            if len(args) >= 1:
                symbol = args[0]
            else:
                symbol = kwargs.get('symbol', '')
        else:
            symbol = kwargs.get('symbol', '')
        
        query = kwargs.get('query', '')
        
        # Create combined query for semantic analysis
        combined_query = f"{symbol} {query}".strip()
        
        # Check if this query is actually asking for cryptocurrency prices
        if combined_query and not is_crypto_query(combined_query):
            return {
                "result": {
                    "status": "error",
                    "message": "This query appears to be asking for stock prices, not cryptocurrency prices. Please use the get_stock_price tool instead.",
                    "error_code": "WRONG_TOOL_TYPE",
                    "suggested_tool": "get_stock_price"
                },
                    "method": "wrong_tool_type",
                    "query_analyzed": combined_query,
                    "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                    "matched_task": False,
                    "multi_call": False,
                    "matched_task_id": None
                }
            }
        
        # If no symbol provided, try to extract from query
        if not symbol and query:
            symbol = get_crypto_symbol_from_query(query)
        
        # Normalize symbol
        if symbol:
            symbol = symbol.upper().strip()
        
        # Create search query for matching
        search_query = f"{symbol} {query}".strip()
        
        # Priority 1: Check if task context is active and has data
        if task_context.is_task_active():
            current_task_id = task_context.get_current_task_id()
            if current_task_id and current_task_id in TASK_DATA:
                task_data = TASK_DATA[current_task_id]
                
                # For multi-call tasks, find the best matching call within the task
                if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                    best_call_index = None
                    best_score = -1
                    
                    # Build query string for matching
                    def build_query_string(call_data):
                        parts = []
                        if call_data.get('symbol'):
                            parts.append(call_data['symbol'])
                        if call_data.get('query'):
                            parts.append(call_data['query'])
                        return ' '.join(parts).strip()
                    
                    for i, call_data in enumerate(task_data['calls']):
                        call_query = build_query_string(call_data)
                        
                        # Calculate query similarity using SequenceMatcher
                        if search_query and call_query:
                            score = SequenceMatcher(None, search_query.lower(), call_query.lower()).ratio()
                            if score > best_score:
                                best_score = score
                                best_call_index = i
                        elif not search_query and not call_query:
                            # Both are empty - consider it a match
                            best_call_index = i
                            break
                    
                    # If no good match found, fallback to first call
                    if best_call_index is None and task_data['calls']:
                        best_call_index = 0
                        best_score = 0.0
                    
                    if best_call_index is not None:
                        call_data = task_data['calls'][best_call_index]
                        result = call_data.get('result', DEFAULT_CRYPTO_RESULT).copy()
                            'method': 'task_context',
                            'matched_task_id': current_task_id,
                            'call_index': best_call_index,
                            'task_active': True,
                            'query_used': search_query,
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
                    result = task_data.get('result', DEFAULT_CRYPTO_RESULT).copy()
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': None,
                        'task_active': True,
                        'query_used': search_query,
                        'task_id': current_task_id,
                        'scenario': task_data.get('scenario', 'unknown'),
                        'matched_task': True,
                        'multi_call': False
                    }
                    return {
                        'result': result,
                    }
        
        # Priority 2: Fallback to intelligent matching
        task_id, task_data, call_index = find_best_matching_task(search_query, symbol)
        
        if task_data and 'result' in task_data:
            # Return the result from matched task
            result = task_data['result'].copy()
            
            # Add debug metadata
                'method': 'similarity_match',
                'matched_task_id': task_id,
                'call_index': call_index,
                'query_used': search_query,
                'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                'matched_task': True,
                'multi_call': call_index is not None
            }
            
            # Ensure consistent format
            if 'status' not in result:
                result['status'] = 'success'
            
            return {
                'result': result,
            }
        
        # No match found, return default result
        default_result = DEFAULT_CRYPTO_RESULT.copy()
        
        # Customize default result based on input
        if symbol:
            default_result['crypto_symbol'] = symbol
            
            # Set different default prices for different symbols
            price_map = {
                'BTC': 68500.00,
                'ETH': 3500.00,
                'USDT': 1.00,
                'XLM': 0.11,
                'XMR': 150.00
            }
            default_result['price'] = price_map.get(symbol, 100.00)
        
        # Add debug metadata
            'method': 'fallback',
            'query_used': search_query,
            'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            'matched_task': False,
            'multi_call': False,
            'matched_task_id': None
        }
        
        return {
            'result': default_result,
        }
        
    except Exception as e:
        return {
            "result": {
                "status": "error",
                "message": f"Failed to retrieve cryptocurrency price: {str(e)}",
                "error_code": "CRYPTO_PRICE_ERROR"
            },
                "method": "exception_fallback",
                "error": str(e),
                "task_active": False,
                "matched_task": False,
                "multi_call": False,
                "matched_task_id": None
            }
        }

def calculate_call_similarity(call_data: Dict[str, Any], query: str, symbol: str = None) -> float:
    """
    Calculate similarity between call data and query/symbol
    
    Args:
        call_data: Call data containing queries and other info
        query: Query string to match
        symbol: Cryptocurrency symbol
    
    Returns:
        Similarity score between 0 and 1
    """
    if not call_data:
        return 0.0
    
    call_queries = call_data.get('queries', [])
    if not call_queries:
        return 0.0
    
    # Calculate priority based on symbol matching
    priority_score = calculate_crypto_priority(query, symbol)
    
    # Calculate query similarity
    max_query_similarity = 0.0
    for call_query in call_queries:
        similarity = calculate_query_similarity(query, call_query)
        max_query_similarity = max(max_query_similarity, similarity)
    
    # Combine scores
    total_score = (priority_score * 0.6) + (max_query_similarity * 0.4)
    return total_score

def find_best_matching_task(query: str, symbol: str = None, call_index: int = None) -> tuple:
    """
    Find the best matching task for the given query and symbol
    
    Args:
        query: Query string to match
        symbol: Cryptocurrency symbol
        call_index: Specific call index to match (optional)
    
    Returns:
        Tuple of (task_id, task_data, call_index) or (None, None, None) if no good match
    """
    if not query and not symbol:
        return (None, None, None)
    
    best_task_id = None
    best_task_data = None
    best_call_index = None
    best_score = 0.0
    
    for task_id, task_data in TASK_DATA.items():
        # Handle calls structure
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            for idx, call_data in enumerate(task_data['calls']):
                # If specific call_index is requested, only check that call
                if call_index is not None and idx != call_index:
                    continue
                
                call_sim = calculate_call_similarity(call_data, query, symbol)
                
                # Update best match if this score is better
                if call_sim > best_score and call_sim > 0.3:  # Minimum threshold
                    best_score = call_sim
                    best_task_id = task_id
                    best_task_data = task_data
                    best_call_index = idx
        else:
            # Handle legacy structure (no calls)
            task_queries = task_data.get('queries', [])
            
            # Calculate priority based on symbol matching
            priority_score = calculate_crypto_priority(query, symbol)
            
            # Calculate query similarity
            max_query_similarity = 0.0
            for task_query in task_queries:
                similarity = calculate_query_similarity(query, task_query)
                max_query_similarity = max(max_query_similarity, similarity)
            
            # Combine scores
            total_score = (priority_score * 0.6) + (max_query_similarity * 0.4)
            
            # Update best match if this score is better
            if total_score > best_score and total_score > 0.3:  # Minimum threshold
                best_score = total_score
                best_task_id = task_id
                best_task_data = task_data
                best_call_index = None  # No call index for legacy structure
    
    return (best_task_id, best_task_data, best_call_index)

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
    
    return normalize_crypto_query(query)

def generate_fallback_response(symbol: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific match is found
    
    Args:
        symbol: Cryptocurrency symbol
    
    Returns:
        Default cryptocurrency price response
    """
    result = DEFAULT_CRYPTO_RESULT.copy()
    
    if symbol:
        result['crypto_symbol'] = symbol.upper()
        
        # Randomize price slightly for variety
        base_prices = {
            'BTC': 68500.00,
            'ETH': 3500.00,
            'USDT': 1.00,
            'XLM': 0.11,
            'XMR': 150.00
        }
        
        base_price = base_prices.get(symbol.upper(), 100.00)
        # Add small random variation (±2%)
        variation = random.uniform(-0.02, 0.02)
        result['price'] = round(base_price * (1 + variation), 2)
    
    return result

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_crypto_price",
        "description": "Get current price of cryptocurrency",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Cryptocurrency symbol (e.g., 'BTC', 'ETH')"
                },
                "query": {
                    "type": "string", 
                    "description": "Query string for matching (optional)"
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
        name="get_crypto_price",
        function=get_crypto_price,
        schema=TOOL_SCHEMA,
        description="Tool function for get_crypto_price"
    )

# Auto-register when module is imported
register_tool()
