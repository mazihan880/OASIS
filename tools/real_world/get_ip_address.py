#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_ip_address tool implementation
Get IP address for a given domain name or hostname
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
    from ..resource.get_ip_address_data import TASK_DATA, DEFAULT_IP_RESULT, DOMAIN_ALIASES
except ImportError:
    TASK_DATA = {}
    DEFAULT_IP_RESULT = {
        "status": "completed",
        "message": "IP address lookup completed successfully",
        "ip_address": "192.168.1.1",
        "query_time": "2024-01-15 10:30:00",
        "dns_server": "8.8.8.8"
    }
    DOMAIN_ALIASES = {
        "google": ["google.com", "www.google.com", "google.co.uk"],
        "github": ["github.com", "www.github.com", "api.github.com"],
        "stackoverflow": ["stackoverflow.com", "www.stackoverflow.com"],
        "wikipedia": ["wikipedia.org", "en.wikipedia.org", "www.wikipedia.org"],
        "youtube": ["youtube.com", "www.youtube.com", "m.youtube.com"],
        "facebook": ["facebook.com", "www.facebook.com", "m.facebook.com"],
        "twitter": ["twitter.com", "www.twitter.com", "x.com"],
        "amazon": ["amazon.com", "www.amazon.com", "aws.amazon.com"],
        "microsoft": ["microsoft.com", "www.microsoft.com", "azure.microsoft.com"],
        "apple": ["apple.com", "www.apple.com", "developer.apple.com"]
    }

def normalize_domain(domain: str) -> str:
    """
    Normalize domain name by removing protocol, www, and trailing dots
    
    Args:
        domain: Domain name to normalize
    
    Returns:
        Normalized domain name
    """
    if not domain:
        return ""
    
    # Remove protocol
    domain = re.sub(r'^https?://', '', domain.lower().strip())
    
    # Remove www prefix
    domain = re.sub(r'^www\.', '', domain)
    
    # Remove trailing dots and slashes
    domain = domain.rstrip('./').strip()
    
    # Extract domain from path if present
    if '/' in domain:
        domain = domain.split('/')[0]
    
    return domain

def domains_match(domain1: str, domain2: str) -> bool:
    """
    Check if two domains are equivalent (considering normalization)
    
    Args:
        domain1: First domain
        domain2: Second domain
    
    Returns:
        True if domains match, False otherwise
    """
    if not domain1 or not domain2:
        return False
    
    norm1 = normalize_domain(domain1)
    norm2 = normalize_domain(domain2)
    
    return norm1 == norm2

def calculate_domain_priority(task_query: str, domain: str = None) -> float:
    """
    Calculate priority score based on domain matching
    
    Args:
        task_query: The task query string to match against
        domain: Domain name to resolve
    
    Returns:
        Priority score (0.0 to 1.0)
    """
    score = 0.0
    
    if not domain:
        return score
    
    query_lower = task_query.lower()
    domain_lower = domain.lower()
    
    # Exact domain match
    if domain_lower in query_lower or normalize_domain(domain) in normalize_domain(query_lower):
        score += 0.8
    
    # Check for domain aliases
    for main_domain, aliases in DOMAIN_ALIASES.items():
        if any(alias.lower() == domain_lower for alias in aliases):
            if main_domain in query_lower or any(alias.lower() in query_lower for alias in aliases):
                score += 0.6
                break
    
    # DNS/IP lookup keywords
    dns_keywords = ['ip', 'address', 'resolve', 'lookup', 'dns', 'nslookup', 'dig', 'ping', 'domain']
    for keyword in dns_keywords:
        if keyword in query_lower:
            score += 0.1
            break
    
    return min(score, 1.0)

def extract_domain_from_query(query_text: str) -> str:
    """
    Extract domain name from query text using improved patterns
    
    Args:
        query_text: Text to extract domain from
    
    Returns:
        Extracted domain name or empty string
    """
    if not query_text:
        return ""
    
    # Domain patterns to match
    domain_patterns = [
        # Explicit domain mentions with backticks or quotes
        r'`([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})`',
        r'"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"',
        r"'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'",
        
        # Standard domain patterns
        r'\b([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b',
        
        # Domain with protocol
        r'https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        
        # www. domains
        r'\bwww\.([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
    ]
    
    for pattern in domain_patterns:
        matches = re.findall(pattern, query_text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                domain = match[0] if match else ""
            else:
                domain = match
            
            # Clean and validate domain
            domain = domain.strip('.,!?;:"\'()[]{}/')
            
            # Skip invalid domains
            if (len(domain) > 3 and 
                '.' in domain and 
                not domain.startswith('.') and 
                not domain.endswith('.') and
                not any(char in domain for char in [' ', '\t', '\n']) and
                not domain.endswith('.local') and  # Skip .local domains
                not domain.startswith('www.www.')):  # Skip malformed domains
                return domain
    
    return ""

def get_ip_address(*args, **kwargs) -> Dict[str, Any]:
    """
    Get IP address for a given domain name or hostname
    
    Args:
        domain: Domain name or hostname to resolve
    
    Returns:
        Dictionary containing the IP address information or error message
    """
    try:
        # Handle both positional and keyword arguments
        if args:
            domain = args[0]
        else:
            domain = kwargs.get('domain') or kwargs.get('hostname') or kwargs.get('target', '')
        
        # If no domain provided, try to extract from query context
        if not domain:
            # Try to get query from kwargs or context
            query_text = kwargs.get('query', '') or kwargs.get('prompt', '') or str(kwargs)
            domain = extract_domain_from_query(query_text)
        
        # If still no domain, check for special cases
        if not domain:
            query_text = str(kwargs).lower()
            
            # Check for local server/IP requests
            if any(keyword in query_text for keyword in ['local ip', 'server ip', 'my ip', 'local address', 'server address']):
                result = {
                    "status": "success",
                    "message": "Local server IP address retrieved",
                    "ip_address": "192.168.1.100",
                    "domain": "localhost",
                    "note": "Local server IP address"
                }
                    'method': 'local_ip_detection',
                    'task_active': False,
                    'domain_used': domain if 'domain' in locals() else None,
                    'matched_task': False,
                    'multi_call': False,
                    'matched_task_id': None
                }
                return {
                    "result": result,
                }
            
            # If no domain can be determined, return error
            result = {
                "status": "error",
                "message": "Unable to extract domain from prompt",
                "ip_address": None
            }
                'method': 'no_domain_error',
                'task_active': False,
                'domain_used': None,
                'matched_task': False,
                'multi_call': False,
                'matched_task_id': None
            }
            return {
                "result": result,
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
                    
                    # Build query string for matching
                    def build_query_string(domain_name):
                        return f"get ip address of {domain_name}"
                    
                    query_string = build_query_string(domain)
                    
                    for i, call_data in enumerate(task_data['calls']):
                        call_domain = call_data.get('domain', '')
                        
                        # Try exact domain match first
                        if domains_match(domain, call_domain):
                            best_call_index = i
                            best_score = 1.0
                            break
                        
                        # Calculate query similarity using SequenceMatcher
                        call_query_string = build_query_string(call_domain)
                        score = SequenceMatcher(None, query_string.lower(), call_query_string.lower()).ratio()
                        if score > best_score:
                            best_score = score
                            best_call_index = i
                    
                    # If no good match found, fallback to first call
                    if best_call_index is None and task_data['calls']:
                        best_call_index = 0
                        best_score = 0.0
                    
                    if best_call_index is not None:
                        call_data = task_data['calls'][best_call_index]
                        result = call_data.get('result', DEFAULT_IP_RESULT).copy()
                            'method': 'task_context',
                            'matched_task_id': current_task_id,
                            'call_index': best_call_index,
                            'best_score': best_score,
                            'task_active': True,
                            'domain_used': domain,
                            'task_id': current_task_id,
                            'scenario': task_data.get('scenario', 'unknown'),
                            'matched_task': True,
                            'multi_call': True
                        }
                        return {
                            "result": result,
                        }
                else:
                    # Single call task - use task-level result directly
                    result = task_data.get('result', DEFAULT_IP_RESULT).copy()
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': None,
                        'task_active': True,
                        'domain_used': domain,
                        'task_id': current_task_id,
                        'scenario': task_data.get('scenario', 'unknown'),
                        'matched_task': True,
                        'multi_call': False
                    }
                    return {
                        "result": result,
                    }
        
        # Priority 2: Fallback to intelligent matching
        # Normalize the domain for matching
        normalized_domain = normalize_domain(domain)
        
        # Try to find exact match first
        for task_id, task_data in TASK_DATA.items():
            task_domain = task_data.get('domain_or_ip', '')
            if domains_match(domain, task_domain):
                 result = {
                     "status": "success",
                     "message": "IP address lookup completed successfully",
                     "ip_address": task_data['result'],
                     "domain": task_domain
                 }
                     'method': 'exact_match',
                     'matched_task_id': task_id,
                     'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                     'domain_used': domain,
                     'matched_task': True,
                     'multi_call': False
                 }
                 return {
                     "result": result,
                 }
        
        # If no exact match, try to find best matching task based on query patterns
        query_str = f"get ip address of {domain}"
        matching_task = find_best_matching_task(query_str, domain=domain)
        
        if matching_task:
            task_id, task_data, score = matching_task
            result = {
                "status": "success",
                "message": "IP address lookup completed successfully",
                "ip_address": task_data['result'],
                "domain": task_data.get('domain_or_ip', domain)
            }
                'method': 'similarity_match',
                'matched_task_id': task_id,
                'match_score': score,
                'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                'domain_used': domain,
                'matched_task': True,
                'multi_call': False
            }
            return {
                "result": result,
            }
        
        # Generate fallback response
        result = generate_fallback_response(domain=domain)
            'method': 'fallback',
            'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            'domain_used': domain,
            'matched_task': False,
            'multi_call': False,
            'matched_task_id': None
        }
        return {
            "result": result,
        }
        
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Failed to get IP address: {str(e)}",
            "ip_address": None
        }
            'method': 'exception_fallback',
            'error': str(e),
            'task_active': False,
            'domain_used': domain if 'domain' in locals() else None,
            'matched_task': False,
            'multi_call': False,
            'matched_task_id': None
        }
        return {
            "result": result,
        }

def extract_ip_from_result(result_str: str) -> str:
    """
    Extract IP address from result string using regex
    
    Args:
        result_str: Result string containing IP address
    
    Returns:
        Extracted IP address or default
    """
    # Look for IP address patterns
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    ip_match = re.search(ip_pattern, result_str)
    if ip_match:
        return ip_match.group(0)
    
    # Return default IP if none found
    return "192.168.1.1"

def find_best_matching_task(query: str, domain: str = None) -> Optional[tuple]:
    """
    Find the best matching task for the given query and domain
    
    Args:
        query: Query string to match
        domain: Domain name to resolve
    
    Returns:
        Tuple of (task_id, task_data, score) for best match, or None
    """
    if not TASK_DATA:
        return None
    
    best_match = None
    best_score = 0.0
    
    normalized_query = normalize_query(query)
    
    for task_id, task_data in TASK_DATA.items():
        # Calculate domain-based priority
        domain_score = calculate_domain_priority(query, domain) if domain else 0.0
        
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
        
        # Domain exact match bonus
        task_domain = task_data.get('domain_or_ip', '')
        if domain and domains_match(domain, task_domain):
            domain_score += 0.5
        
        # Combined score with adjusted weights
        total_score = (query_score * 0.7) + (domain_score * 0.3)
        
        # When task context is active, remove threshold to always return best match
        threshold = 0.0 if (hasattr(task_context, 'is_task_active') and task_context.is_task_active()) else 0.2
        if total_score > best_score and total_score > threshold:
            best_score = total_score
            best_match = (task_id, task_data, total_score)
    
    return best_match

def normalize_query(query: str) -> str:
    """Normalize query string for better matching"""
    if not query:
        return ""
    
    # Convert to lowercase and remove extra whitespace
    normalized = re.sub(r'\s+', ' ', query.lower().strip())
    
    # Remove common DNS lookup prefixes
    normalized = re.sub(r'^(get ip of|resolve|lookup|ip address of|dns lookup|nslookup|dig|ping|check ip|domain to ip|resolve hostname|resolve domain|find ip|get ip address for)\s*', '', normalized)
    
    # Remove JSON formatting
    normalized = re.sub(r'[{}"\']', '', normalized)
    normalized = re.sub(r'(domain|target|hostname):\s*', '', normalized)
    
    return normalized

def generate_fallback_response(domain: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no matching task is found
    
    Args:
        domain: Domain that was requested
    
    Returns:
        Fallback response dictionary
    """
    if not domain:
        result = {
            "status": "error",
            "message": "Domain parameter is required",
            "ip_address": None
        }
        return {
            "result": result
        }
    
    # Generate a realistic IP based on domain type
    normalized_domain = normalize_domain(domain)
    
    if '.local' in normalized_domain or '.internal' in normalized_domain:
        # Local/internal domains get private IP ranges
        ip_address = "192.168.1.100"
    elif '.gov' in normalized_domain:
        # Government domains
        ip_address = "203.0.113.55"
    elif 'github' in normalized_domain:
        # GitHub pages
        ip_address = "185.199.108.153"
    elif any(tld in normalized_domain for tld in ['.com', '.org', '.net']):
        # Public domains
        ip_address = "198.51.100.42"
    else:
        # Default
        ip_address = "192.168.1.1"
    
    result = {
        "status": "success",
        "message": "IP address lookup completed successfully",
        "ip_address": ip_address,
        "domain": domain,
        "fallback": True
    }
    return {
        "result": result
    }

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_ip_address",
        "description": "Get IP address for a given domain name or hostname",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Domain name or hostname to resolve"
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
        name="get_ip_address",
        function=get_ip_address,
        schema=TOOL_SCHEMA,
        description="Tool function for get_ip_address"
    )

# Auto-register when module is imported
register_tool()
