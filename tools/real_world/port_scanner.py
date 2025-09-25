#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
port_scanner tool implementation
Scan target IP addresses for open ports
"""

import json
import random
import re
import time
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
    from ..resource.port_scanner_data import TASK_DATA, DEFAULT_PORT_SCANNER_RESULT
except ImportError:
    TASK_DATA = {}
    DEFAULT_PORT_SCANNER_RESULT = {
        "status": "success",
        "target_ip": "localhost",
        "open_ports": [
            {"port": 80, "service": "http"},
            {"port": 443, "service": "https"}
        ],
        "message": "Port scan completed successfully"
    }

def build_query_string(*args, **kwargs) -> str:
    """
    Build a query string from function arguments for similarity matching
    """
    query_parts = []
    
    # Add positional arguments
    for arg in args:
        if arg is not None:
            query_parts.append(str(arg).strip())
    
    # Add keyword arguments
    for key, value in kwargs.items():
        if value is not None:
            query_parts.append(f"{key}:{str(value).strip()}")
    
    return " ".join(query_parts)

def port_scanner(*args, **kwargs) -> Dict[str, Any]:
    """
    Scan target IP addresses or hostnames for open ports
    
    Args:
        *args: Positional arguments (target)
        **kwargs: Keyword arguments (target)
    
    Returns:
        Dict containing the port scan results
    """
    
    try:
        # Extract target parameter
        target = None
        
        # Handle positional arguments
        if len(args) >= 1:
            target = str(args[0]).strip()
        
        # Handle keyword arguments
        target = kwargs.get('target', target)
        
        if not target:
            return {
                "result": {
                    "status": "error",
                    "message": "No target specified for port scanning",
                    "error_code": "MISSING_TARGET",
                    "target_ip": "",
                    "open_ports": []
                }
            }
        
        # Priority 1: Check if task context is active and has data
        if task_context.is_task_active():
            current_task_id = task_context.get_current_task_id()
            if current_task_id and current_task_id in TASK_DATA:
                task_data = TASK_DATA[current_task_id]
                
                # For multi-call tasks, find the best matching call within the task
                if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                    current_query = build_query_string(*args, **kwargs)
                    best_match_index = None
                    best_score = -1
                    
                    for i, call_data in enumerate(task_data['calls']):
                        call_query = call_data.get('query', '')
                        
                        # Calculate query similarity score
                        score = SequenceMatcher(None, current_query.lower(), call_query.lower()).ratio()
                        if score > best_score:
                            best_score = score
                            best_match_index = i
                    
                    # Use best match or fallback to first call
                    if best_match_index is not None:
                        call_data = task_data['calls'][best_match_index]
                        call_result = call_data.get('result', DEFAULT_PORT_SCANNER_RESULT)
                        
                        # Build result structure
                        if isinstance(call_result, dict):
                            result = call_result.copy()
                        else:
                            result = {
                                "status": "success",
                                "target_ip": str(target),
                                "open_ports": [],
                                "message": str(call_result)
                            }
                        
                        return {
                            "result": result,
                                'method': 'task_context',
                                'matched_task_id': current_task_id,
                                'call_index': best_match_index,
                                'task_active': True,
                                'query_used': current_query,
                                'best_score': best_score,
                                'task_id': current_task_id,
                                'scenario': task_data.get('scenario', 'unknown'),
                                'matched_task': True,
                                'multi_call': True
                            }
                        }
                    else:
                        # Fallback to first call if no match found
                        call_data = task_data['calls'][0]
                        call_result = call_data.get('result', DEFAULT_PORT_SCANNER_RESULT)
                        
                        # Build result structure
                        if isinstance(call_result, dict):
                            result = call_result.copy()
                        else:
                            result = {
                                "status": "success",
                                "target_ip": str(target),
                                "open_ports": [],
                                "message": str(call_result)
                            }
                        
                        return {
                            "result": result,
                                'method': 'task_context_fallback',
                                'matched_task_id': current_task_id,
                                'call_index': 0,
                                'task_active': True,
                                'query_used': current_query,
                                'task_id': current_task_id,
                                'scenario': task_data.get('scenario', 'unknown'),
                                'matched_task': True,
                                'multi_call': True
                            }
                        }
                else:
                    # Single call task - use task-level result directly
                    task_result = task_data.get('result', DEFAULT_PORT_SCANNER_RESULT)
                    
                    # Build result structure
                    if isinstance(task_result, dict):
                        result = task_result.copy()
                    else:
                        result = {
                            "status": "success",
                            "target_ip": str(target),
                            "open_ports": [],
                            "message": str(task_result)
                        }
                    
                    return {
                        "result": result,
                            'method': 'task_context',
                            'matched_task_id': current_task_id,
                            'call_index': None,
                            'task_active': True,
                            'target_used': target,
                            'task_id': current_task_id,
                            'scenario': task_data.get('scenario', 'unknown'),
                            'matched_task': True,
                            'multi_call': False
                        }
                    }
        
        # Priority 2: Fallback to intelligent matching
        # Normalize the target
        normalized_target = normalize_target(target)
        
        # Try to find matching task data
        matching_task = find_best_matching_task(normalized_target)
        
        if matching_task:
            task_id, task_data = matching_task
            task_result = task_data["result"]
            
            # Build result structure
            if isinstance(task_result, dict):
                result = task_result.copy()
            else:
                result = {
                    "status": "success",
                    "target_ip": str(target),
                    "open_ports": [],
                    "message": str(task_result)
                }
            
            return {
                "result": result,
                    'method': 'similarity_match',
                    'matched_task_id': task_id,
                    'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                    'target_used': target,
                    'matched_target': normalized_target,
                    'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    'matched_task': True,
                    'multi_call': False
                }
            }
        
        # If no specific task matches, return default response
        fallback_result = generate_fallback_response(normalized_target)
        return {
            "result": fallback_result,
                'method': 'fallback',
                'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                'target_used': target,
                'matched_task': False,
                'multi_call': False,
                'matched_task_id': None
            }
        }
        
    except Exception as e:
        # Ensure no errors are raised - return safe default
        return {
            "result": {
                "status": "success",
                "target_ip": str(target or "unknown"),
                "open_ports": [
                    {"port": 80, "service": "http"},
                    {"port": 443, "service": "https"}
                ],
                "message": "Port scan completed successfully",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "note": "Default response - sandbox environment"
            },
                'method': 'exception_fallback',
                'error': str(e),
                'task_active': False,
                'target_used': target if 'target' in locals() else None
            }
        }

def find_best_matching_task(target: str) -> Optional[tuple]:
    """
    Find the best matching task for the given target
    
    Args:
        target: Normalized target to search for
    
    Returns:
        Tuple of (task_id, task_data) if found, None otherwise
    """
    
    if not TASK_DATA:
        return None
    
    best_match = None
    best_score = 0.0
    
    for task_id, task_data in TASK_DATA.items():
        queries = task_data.get("queries", [])
        
        for query in queries:
            # Normalize query for comparison
            normalized_query = normalize_target(query)
            
            # Exact match gets highest priority
            if normalized_query == target:
                return (task_id, task_data)
            
            # Calculate similarity score
            similarity = SequenceMatcher(None, normalized_query, target).ratio()
            
            # Check if target is contained in query or vice versa
            if target in normalized_query or normalized_query in target:
                similarity = max(similarity, 0.8)
            
            # Special handling for IP addresses
            if is_ip_address(target) and is_ip_address(normalized_query):
                if target == normalized_query:
                    return (task_id, task_data)
                elif target.split('.')[0:3] == normalized_query.split('.')[0:3]:  # Same subnet
                    similarity = max(similarity, 0.7)
            
            # Special handling for hostnames
            if is_hostname(target) and is_hostname(normalized_query):
                # Check domain similarity
                target_parts = target.split('.')
                query_parts = normalized_query.split('.')
                if len(target_parts) > 1 and len(query_parts) > 1:
                    if target_parts[-2:] == query_parts[-2:]:  # Same domain
                        similarity = max(similarity, 0.8)
            
            # Update best match if this is better
            if similarity > best_score and similarity > 0.6:  # Minimum threshold
                best_match = (task_id, task_data)
                best_score = similarity
    
    return best_match

def normalize_target(target: str) -> str:
    """
    Normalize a target string for consistent matching
    
    Args:
        target: Raw target string
    
    Returns:
        Normalized target string
    """
    if not target:
        return ""
    
    # Convert to lowercase and remove extra whitespace
    normalized = target.lower().strip()
    
    # Remove common prefixes
    prefixes = ['scan ', 'port scan ', 'check ', 'nmap ']
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
    
    # Remove common suffixes
    suffixes = [' ports', ' open ports', ' scan', ' port scan']
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    return normalized

def is_ip_address(text: str) -> bool:
    """Check if text is an IP address"""
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$'
    return bool(re.match(ip_pattern, text))

def is_hostname(text: str) -> bool:
    """Check if text is a hostname"""
    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(hostname_pattern, text))

def generate_fallback_response(target: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific task matches
    
    Args:
        target: The target being scanned
    
    Returns:
        Default port scan response
    """
    
    # Use default result as base
    result = DEFAULT_PORT_SCANNER_RESULT.copy()
    
    if target:
        result["target_ip"] = target
        
        # Generate realistic-looking ports based on target hash
        port_seed = hash(target) % 100
        if port_seed < 30:
            # Common web ports
            result["open_ports"] = [
                {"port": 80, "service": "http"},
                {"port": 443, "service": "https"}
            ]
        elif port_seed < 60:
            # SSH + web
            result["open_ports"] = [
                {"port": 22, "service": "ssh"},
                {"port": 80, "service": "http"},
                {"port": 443, "service": "https"}
            ]
        else:
            # No open ports
            result["open_ports"] = []
        
        result["message"] = f"Port scan completed for {target}"
    
    result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    result["note"] = "Default response - no specific task match found"
    
    return result

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "port_scanner",
        "description": "Scan target IP addresses or hostnames for open ports",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target IP address, hostname, or network range to scan (e.g., 192.168.1.1, example.com, 10.0.1.0/24)"
                }
            },
            "required": ["target"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="port_scanner",
        function=port_scanner,
        schema=TOOL_SCHEMA,
        description="Tool function for port_scanner"
    )

# Auto-register when module is imported
register_tool()
