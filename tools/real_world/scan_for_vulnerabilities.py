#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_for_vulnerabilities tool implementation
Scan target systems for security vulnerabilities
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
    from ..resource.scan_for_vulnerabilities_data import TASK_DATA, DEFAULT_SCAN_RESULT
except ImportError:
    try:
        # Fallback to absolute import
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'resource'))
        from scan_for_vulnerabilities_data import TASK_DATA, DEFAULT_SCAN_RESULT
    except ImportError:
        TASK_DATA = {}
        DEFAULT_SCAN_RESULT = {
            "status": "success",
            "target": "localhost",
            "vulnerabilities_found": [],
            "message": "Vulnerability scan completed successfully"
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

def scan_for_vulnerabilities(*args, **kwargs) -> Dict[str, Any]:
    """
    Scan target systems for security vulnerabilities
    
    Args:
        *args: Positional arguments (target)
        **kwargs: Keyword arguments (target)
    
    Returns:
        Dict containing the vulnerability scan results
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
            result = {
                "status": "error",
                "message": "No target specified for vulnerability scanning",
                "error_code": "MISSING_TARGET"
            }
                'method': 'error_missing_target',
                'task_active': False
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
                        result = call_data.get('result', DEFAULT_SCAN_RESULT).copy()
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
                    else:
                        # Fallback to first call if no match found
                        call_data = task_data['calls'][0]
                        result = call_data.get('result', DEFAULT_SCAN_RESULT).copy()
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
                else:
                    # Single call task - use task-level result directly
                    result = task_data.get('result', DEFAULT_SCAN_RESULT).copy()
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
        
        # Priority 2: Fallback to intelligent matching
        # Normalize the target
        normalized_target = normalize_target(target)
        
        # Try to find matching task data
        matching_task = find_best_matching_task(normalized_target)
        
        if matching_task:
            task_id, task_data = matching_task
            result = task_data["result"].copy()
            
            # Add debug metadata
                'method': 'similarity_match',
                'matched_task_id': task_id,
                'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
                'target_used': target,
                'task_id': task_id,
                'matched_target': normalized_target,
                'matched_task': True,
                'multi_call': False
            }
            result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            
        
        # If no specific task matches, return default response
        result = generate_fallback_response(normalized_target)
            'method': 'fallback',
            'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            'target_used': target,
            'matched_task': False,
            'multi_call': False,
            'matched_task_id': None
        }
        
    except Exception as e:
        # Ensure no errors are raised - return safe default
        result = {
            "status": "success",
            "target": str(target or "unknown"),
            "vulnerabilities_found": [],
            "message": "Vulnerability scan completed successfully",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": "Default response - sandbox environment"
        }
            'method': 'exception_fallback',
            'error': str(e),
            'task_active': False,
            'target_used': target if 'target' in locals() else None
        }

def find_best_matching_task(target: str) -> Optional[tuple]:
    """
    Find the best matching task for the given target
    
    Args:
        target: Normalized target to search for
    
    Returns:
        Tuple of (task_id, task_data) if found, None otherwise
    """
    
    best_match = None
    best_score = 0.0
    
    for task_id, task_data in TASK_DATA.items():
        queries = task_data.get("queries", [])
        
        for query in queries:
            # Normalize the query for comparison
            normalized_query = normalize_target(query)
            
            # Check for exact match first
            if target.lower() == normalized_query.lower():
                return (task_id, task_data)
            
            # Calculate similarity score
            similarity = SequenceMatcher(None, target.lower(), normalized_query.lower()).ratio()
            
            # Check for exact matches or high similarity
            if similarity > best_score:
                best_score = similarity
                best_match = (task_id, task_data)
            
            # Check for substring matches
            if target.lower() in normalized_query.lower() or normalized_query.lower() in target.lower():
                if similarity > 0.5:  # Ensure reasonable similarity
                    return (task_id, task_data)
    
    # Return best match if similarity is high enough
    if best_score > 0.8:
        return best_match
    
    return None

def normalize_target(target: str) -> str:
    """
    Normalize target for consistent matching
    
    Args:
        target: Raw target string
    
    Returns:
        Normalized target string
    """
    
    # Remove common prefixes and suffixes
    target = target.strip()
    
    # Remove protocol prefixes
    target = re.sub(r'^https?://', '', target)
    target = re.sub(r'^ftp://', '', target)
    
    # Remove port numbers
    target = re.sub(r':\d+$', '', target)
    
    # Remove trailing slashes
    target = target.rstrip('/')
    
    # Handle IP addresses and hostnames
    if is_ip_address(target):
        return target
    elif is_hostname(target):
        return target.lower()
    else:
        # For other formats, return as-is but lowercased
        return target.lower()

def is_ip_address(text: str) -> bool:
    """Check if text is an IP address"""
    return bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', text))

def is_hostname(text: str) -> bool:
    """Check if text is a hostname"""
    return bool(re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', text))

def generate_fallback_response(target: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific match is found
    
    Args:
        target: Target being scanned
    
    Returns:
        Dict containing default vulnerability scan response
    """
    
    # Generate fallback response based on target type
    if target and any(keyword in target.lower() for keyword in ['localhost', '127.0.0.1', 'test', 'demo', 'example']):
        # Safe test environment
        return {
            "status": "completed",
            "target": target,
            "vulnerabilities_found": 2,
            "scan_type": "comprehensive",
            "vulnerabilities": [
                {
                    "type": "Outdated Software",
                    "severity": "Medium",
                    "description": "Some software packages are outdated",
                    "recommendation": "Update to latest versions"
                },
                {
                    "type": "Weak SSL Configuration",
                    "severity": "Low", 
                    "description": "SSL configuration could be strengthened",
                    "recommendation": "Update SSL/TLS configuration"
                }
            ],
            "message": f"Vulnerability scan completed for {target}. Found 2 non-critical issues.",
            "recommendations": [
                "Update software packages regularly",
                "Strengthen SSL/TLS configuration",
                "Implement regular security audits",
                "Use strong authentication methods"
            ],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": "Test environment response"
        }
    else:
        # Production or unknown environment - minimal response
        return {
            "status": "completed",
            "target": target or "unknown",
            "vulnerabilities_found": 0,
            "scan_type": "basic",
            "message": f"Vulnerability scan completed for {target or 'unknown'}. No critical vulnerabilities detected.",
            "recommendations": [
                "Keep software updated",
                "Use strong passwords", 
                "Enable firewall protection",
                "Regular security monitoring"
            ],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": "Default response - sandbox environment"
        }

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "scan_for_vulnerabilities",
        "description": "Scan target systems for security vulnerabilities",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target IP address, hostname, or URL to scan for vulnerabilities (e.g., 192.168.1.1, example.com, https://example.com)"
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
        name="scan_for_vulnerabilities",
        function=scan_for_vulnerabilities,
        schema=TOOL_SCHEMA,
        description="Tool function for scan_for_vulnerabilities"
    )

# Auto-register when module is imported
register_tool()
