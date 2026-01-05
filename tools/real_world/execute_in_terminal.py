#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
execute_in_terminal tool implementation - tasks-Aware Version
Execute shell commands in a sandboxed terminal environment
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
    # Try relative import first
    from ..resource.execute_in_terminal_data import TASK_DATA
except ImportError:
    try:
        # Try absolute import as fallback
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resource_dir = os.path.join(current_dir, '..', 'resource')
        sys.path.insert(0, resource_dir)
        from execute_in_terminal_data import TASK_DATA
    except ImportError:
        # Set empty data if all imports fail
        TASK_DATA = {}

# Set default result
DEFAULT_EXECUTE_RESULT = {"status": "error", "message": "Resource data not available"}

def execute_in_terminal(*args, **kwargs) -> Dict[str, Any]:
    """
    Execute shell commands in a sandboxed terminal environment
    Supports both single tasks and multi-call tasks with calls array.
    
    Args:
        *args: Positional arguments (command, working_directory, etc.)
        **kwargs: Keyword arguments (command, cwd, timeout, etc.)
    
    Returns:
        Dict containing the command execution response
    """
    
    try:
        # Extract command parameters
        command = None
        cwd = None
        timeout = None
        
        # Handle positional arguments
        if len(args) >= 1:
            command = str(args[0])
        if len(args) >= 2:
            cwd = str(args[1])
        if len(args) >= 3:
            timeout = args[2]
        
        # Handle keyword arguments
        if 'command' in kwargs:
            command = str(kwargs['command'])
        if 'cwd' in kwargs:
            cwd = str(kwargs['cwd'])
        if 'working_directory' in kwargs:
            cwd = str(kwargs['working_directory'])
        if 'timeout' in kwargs:
            timeout = kwargs['timeout']
        
        if not command:
            return {
                "result": {
                    "status": "error",
                    "message": "No command provided",
                    "stderr": "Command parameter is required",
                    "return_code": 1
                }
            }
        
        # Priority 1: Use task context data if available
        if task_context.is_task_active():
            current_task_id = task_context.get_current_task_id()
            if current_task_id and current_task_id in TASK_DATA:
                task_data = TASK_DATA[current_task_id]
                
                # Handle calls structure for multi-call tasks
                if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                    # Use similarity matching to find best call
                    best_call = None
                    best_score = -1
                    
                    for call in task_data['calls']:
                        queries = call.get('queries', [])
                        for query in queries:
                            if query:
                                # Calculate similarity between command and query
                                similarity = SequenceMatcher(None, command.lower(), query.lower()).ratio()
                                if similarity > best_score:
                                    best_score = similarity
                                    best_call = call
                    
                    # Use best matching call or fallback to first call
                    if best_call:
                        task_result = best_call['result'].copy()
                    else:
                        task_result = task_data['calls'][0]['result'].copy()
                    
                    # Add command details to response
                    if command:
                        task_result['command'] = command
                    if cwd:
                        task_result['cwd'] = cwd
                    if timeout:
                        task_result['timeout'] = timeout
                    
                    return {
                        'result': task_result,
                            'method': 'task_context',
                            'matched_task_id': current_task_id,
                            'task_active': True,
                            'has_calls': True,
                            'best_score': best_score
                        }
                    }
                else:
                    # Handle single task structure
                    task_result = task_data["result"].copy()
                    
                    # Add command details to response
                    if command:
                        task_result['command'] = command
                    if cwd:
                        task_result['cwd'] = cwd
                    if timeout:
                        task_result['timeout'] = timeout
                    
                    return {
                        'result': task_result,
                            'method': 'task_context',
                            'matched_task_id': current_task_id,
                            'task_active': True,
                            'has_calls': False,
                            'best_score': None
                        }
                    }
        
        # Priority 2: Fallback to intelligent matching
        # Create search query from command
        search_query = command.strip()
        
        # Find best matching task
        best_match = find_best_matching_task(search_query)
        
        if best_match:
            task_id, task_data, call_index = best_match
            
            # Handle multi-call tasks with calls array
            if call_index is not None:
                match_result = task_data['result'].copy()
                
                # Add command details to response
                if 'command' not in match_result:
                    match_result['command'] = command
                if cwd and 'cwd' not in match_result:
                    match_result['cwd'] = cwd
                
                return {
                    'result': match_result,
                        'method': 'similarity_match',
                        'matched_task_id': task_id,
                        'call_index': call_index,
                        'match_type': 'multi_call',
                        'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False
                    }
                }
            else:
                # Handle legacy single task structure
                match_result = task_data['result'].copy()
                
                # Add command details to response
                if 'command' not in match_result:
                    match_result['command'] = command
                if cwd and 'cwd' not in match_result:
                    match_result['cwd'] = cwd
                
                return {
                    'result': match_result,
                        'method': 'similarity_match',
                        'matched_task_id': task_id,
                        'match_type': 'single_task',
                        'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False
                    }
                }
        else:
            # Generate fallback response
            fallback_result = generate_fallback_response(command, cwd)
            return {
                'result': fallback_result,
                    'method': 'fallback',
                    'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False
                }
            }
            
    except Exception as e:
        return {
            "result": {
                "status": "error",
                "message": f"Failed to execute command: {str(e)}",
                "stderr": str(e),
                "return_code": 1
            }
        }

def find_best_matching_task(query: str) -> Optional[tuple]:
    """
    Find the best matching task for the given query
    Supports both single tasks and multi-call tasks with calls array.
    
    Args:
        query: Command string to match
    
    Returns:
        Tuple of (task_id, task_data, call_index) if match found, None otherwise
    """
    
    if not TASK_DATA:
        return None
    
    # Normalize query
    normalized_query = normalize_query(query)
    
    # Find best matching task using improved similarity
    best_match = None
    best_score = 0.0
    min_threshold = 0.4  # Increased threshold to reduce false positives
    
    # Extract key components for better matching
    search_words = set(normalized_query.split())
    
    # Extract command name and parameters for more precise matching
    query_command = extract_command_name(query)
    query_params = extract_parameters(query)
    
    for task_id, task_data in TASK_DATA.items():
        if task_id == "default_normal":
            continue
        
        # Handle new calls array structure for multi-call tasks
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            for call_idx, call_data in enumerate(task_data['calls']):
                queries = call_data.get('queries', [])
                if not queries:
                    continue
                    
                for task_query in queries:
                    if not task_query:
                        continue
                        
                    normalized_task_query = normalize_query(task_query)
                    query_words = set(normalized_task_query.split())
                    
                    # Extract command and parameters from task query
                    task_command = extract_command_name(task_query)
                    task_params = extract_parameters(task_query)
                    
                    # Calculate base similarity
                    score = SequenceMatcher(None, normalized_query, normalized_task_query).ratio()
                    
                    # Apply all the same scoring logic as before
                    if normalized_query == normalized_task_query:
                        score = 1.0
                    elif normalized_query in normalized_task_query or normalized_task_query in normalized_query:
                        score += 0.2
                    
                    if query_command and task_command:
                        if query_command == task_command:
                            score += 0.4
                        elif query_command in task_command or task_command in query_command:
                            score += 0.2
                        else:
                            if query_command != task_command and len(query_command) > 3 and len(task_command) > 3:
                                score *= 0.3
                    
                    param_score = calculate_parameter_similarity(query_params, task_params)
                    score += param_score * 0.3
                    
                    common_words = search_words & query_words
                    if common_words and len(common_words) >= 1:
                        overlap_ratio = len(common_words) / max(len(search_words), len(query_words))
                        if overlap_ratio >= 0.3:
                            score += 0.2 * overlap_ratio
                    
                    if 'python' in search_words and 'python' in query_words:
                        if query_command != task_command:
                            score *= 0.5
                    
                    if query.strip() == task_query.strip():
                        score += 0.5
                    
                    if len(search_words) <= 1:
                        score *= 0.6
                    
                    if score > best_score and score > min_threshold:
                        best_score = score
                        best_match = (task_id, call_data, call_idx)
                    elif score == best_score and score > min_threshold:
                        if best_match and task_id < best_match[0]:
                            best_match = (task_id, call_data, call_idx)
        else:
            # Handle legacy single task structure
            queries = task_data.get('queries', [])
            if not queries:
                continue
                
            for task_query in queries:
                if not task_query:
                    continue
                    
                normalized_task_query = normalize_query(task_query)
                query_words = set(normalized_task_query.split())
                
                # Extract command and parameters from task query
                task_command = extract_command_name(task_query)
                task_params = extract_parameters(task_query)
                
                # Calculate base similarity
                score = SequenceMatcher(None, normalized_query, normalized_task_query).ratio()
                
                # Apply all the same scoring logic
                if normalized_query == normalized_task_query:
                    score = 1.0
                elif normalized_query in normalized_task_query or normalized_task_query in normalized_query:
                    score += 0.2
                
                if query_command and task_command:
                    if query_command == task_command:
                        score += 0.4
                    elif query_command in task_command or task_command in query_command:
                        score += 0.2
                    else:
                        if query_command != task_command and len(query_command) > 3 and len(task_command) > 3:
                            score *= 0.3
                
                param_score = calculate_parameter_similarity(query_params, task_params)
                score += param_score * 0.3
                
                common_words = search_words & query_words
                if common_words and len(common_words) >= 1:
                    overlap_ratio = len(common_words) / max(len(search_words), len(query_words))
                    if overlap_ratio >= 0.3:
                        score += 0.2 * overlap_ratio
                
                if 'python' in search_words and 'python' in query_words:
                    if query_command != task_command:
                        score *= 0.5
                
                if query.strip() == task_query.strip():
                    score += 0.5
                
                if len(search_words) <= 1:
                    score *= 0.6
                
                if score > best_score and score > min_threshold:
                    best_score = score
                    best_match = (task_id, task_data, None)
                elif score == best_score and score > min_threshold:
                    if best_match and task_id < best_match[0]:
                        best_match = (task_id, task_data, None)
            
            # Stop early if we find perfect match
            if score >= 1.0:
                return best_match
    
    return best_match

def extract_command_name(command: str) -> str:
    """
    Extract the main command name from a command string
    """
    if not command:
        return ""
    
    # Remove common prefixes
    command = command.strip()
    if command.startswith('python '):
        # Extract script name after python
        parts = command.split()
        if len(parts) > 1:
            script = parts[1]
            if script.startswith('-c'):
                return 'python-c'  # Special case for python -c
            elif script.startswith('./'):
                return script[2:].split('.')[0]  # Remove ./ and extension
            else:
                return script.split('.')[0]  # Remove extension
        return 'python'
    elif command.startswith('sh '):
        # Extract script name after sh
        parts = command.split()
        if len(parts) > 1:
            script = parts[1]
            return script.split('/')[-1].split('.')[0]  # Get filename without path and extension
        return 'sh'
    else:
        # Extract first word as command
        return command.split()[0] if command.split() else ""

def extract_parameters(command: str) -> dict:
    """
    Extract parameter names and values from a command string
    """
    params = {}
    if not command:
        return params
    
    # Find all --parameter patterns
    import re
    param_pattern = r'--([a-zA-Z-_]+)(?:\s+([^\s-][^\s]*?))?(?=\s--|$)'
    matches = re.findall(param_pattern, command)
    
    for param_name, param_value in matches:
        params[param_name] = param_value.strip('"\'\'') if param_value else True
    
    return params

def calculate_parameter_similarity(params1: dict, params2: dict) -> float:
    """
    Calculate similarity between two parameter dictionaries
    Focus on parameter names rather than values
    """
    if not params1 and not params2:
        return 1.0
    if not params1 or not params2:
        return 0.0
    
    keys1 = set(params1.keys())
    keys2 = set(params2.keys())
    
    # Calculate Jaccard similarity for parameter names
    intersection = len(keys1 & keys2)
    union = len(keys1 | keys2)
    
    if union == 0:
        return 1.0
    
    return intersection / union

def normalize_query(query: str) -> str:
    """Normalize query string"""
    # Convert to lowercase and remove extra spaces
    normalized = re.sub(r'\s+', ' ', query.lower().strip())
    # Remove common punctuation but keep important shell characters
    normalized = re.sub(r'["\'\.\,\?\!\;\:]', '', normalized)
    return normalized

def generate_fallback_response(command: str = None, cwd: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific match is found
    
    Args:
        command: The command that was executed
        cwd: Working directory
    
    Returns:
        Dict containing fallback execution response
    """
    
    response = {
        "status": "success",
        "stdout": "Command executed successfully",
        "stderr": "",
        "return_code": 0
    }
    
    if command:
        response['command'] = command
    if cwd:
        response['cwd'] = cwd
    
    # Generate contextual responses based on command content
    if command:
        command_lower = command.lower()
        if 'ls' in command_lower or 'dir' in command_lower:
            response['stdout'] = "file1.txt  file2.py  directory1/  directory2/"
        elif 'pwd' in command_lower:
            response['stdout'] = cwd if cwd else "/home/user"
        elif 'echo' in command_lower:
            # Extract echo content
            echo_match = re.search(r'echo\s+(.+)', command_lower)
            if echo_match:
                response['stdout'] = echo_match.group(1)
            else:
                response['stdout'] = "Command executed successfully"
        elif 'cat' in command_lower:
            response['stdout'] = "File content displayed successfully"
        elif 'grep' in command_lower:
            response['stdout'] = "Search completed successfully"
        elif 'find' in command_lower:
            response['stdout'] = "Search completed successfully"
        elif 'ps' in command_lower:
            response['stdout'] = "PID  COMMAND\n1234 python\n5678 bash"
        elif 'whoami' in command_lower:
            response['stdout'] = "user"
        elif 'date' in command_lower:
            response['stdout'] = "Mon Sep 12 10:30:00 UTC 2025"
    
    return response

# Tool registration (following web_search pattern)
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_in_terminal",
        "description": "Execute shell commands in a sandboxed terminal environment",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory for command execution (optional)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Command timeout in seconds (optional)"
                }
            },
            "required": ["command"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="execute_in_terminal",
        function=execute_in_terminal,
        schema=TOOL_SCHEMA,
        description="Tool function for execute_in_terminal"
    )

# Auto-register when module is imported
register_tool()
