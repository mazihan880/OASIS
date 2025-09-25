#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translate Text Tool - tasks-Aware Version
Translate text from one language to another
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
        # Add the AgentSafe root directory to path
        agentsafe_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if agentsafe_root not in sys.path:
            sys.path.insert(0, agentsafe_root)
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
    from ..resource.translate_text_data import TASK_DATA, DEFAULT_TRANSLATION_RESULT
except ImportError:
    TASK_DATA = {}
    DEFAULT_TRANSLATION_RESULT = {"status": "error", "message": "Resource data not available"}

def build_query_string(text="", target_language="", source_language="") -> str:
    """
    Build a query string from function arguments for similarity matching
    """
    query_parts = []
    
    if text:
        query_parts.append(f"text:{text.strip()}")
    if target_language:
        query_parts.append(f"target:{target_language.strip()}")
    if source_language:
        query_parts.append(f"source:{source_language.strip()}")
    
    return " ".join(query_parts)

def translate_text(*args, **kwargs) -> Dict[str, Any]:
    """
    Translate text from one language to another with task context support
    
    Args:
        *args: Positional arguments (text, target_language, source_language, etc.)
        **kwargs: Keyword arguments (text, target_language, source_language, etc.)
    
    Returns:
        Dict containing the translation response
    """
    
    try:
        # Extract translation parameters
        text = None
        target_language = None
        source_language = None
        
        # Handle positional arguments
        if len(args) >= 1:
            text = str(args[0])
        if len(args) >= 2:
            target_language = str(args[1])
        if len(args) >= 3:
            source_language = str(args[2])
        
        # Handle keyword arguments
        if 'text' in kwargs:
            text = str(kwargs['text'])
        if 'target_language' in kwargs:
            target_language = str(kwargs['target_language'])
        if 'source_language' in kwargs:
            source_language = str(kwargs['source_language'])
        if 'to_language' in kwargs:
            target_language = str(kwargs['to_language'])
        if 'from_language' in kwargs:
            source_language = str(kwargs['from_language'])
        
        # Priority 1: Check if task context is active and has data
        current_task_id = task_context.get_current_task_id()
        if current_task_id and task_context.is_task_active() and current_task_id in TASK_DATA:
            task_data = TASK_DATA[current_task_id]
            
            # For multi-call tasks, find the best matching call within the task
            if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                current_query = build_query_string(text, target_language, source_language)
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
                    result = call_data.get('result', DEFAULT_TRANSLATION_RESULT).copy()
                    
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': best_match_index,
                        'task_active': True,
                        'matched_task': True,
                        'multi_call': True,
                        'query_used': current_query,
                        'best_score': best_score
                    }
                    return {
                        'result': result,
                    }
                else:
                    # Fallback to first call if no match found
                    call_data = task_data['calls'][0]
                    result = call_data.get('result', DEFAULT_TRANSLATION_RESULT).copy()
                    
                        'method': 'task_context_fallback',
                        'matched_task_id': current_task_id,
                        'call_index': 0,
                        'task_active': True,
                        'matched_task': True,
                        'multi_call': True,
                        'query_used': current_query
                    }
                    return {
                        'result': result,
                    }
            else:
                # Single call task - use task-level result directly
                if task_data and 'result' in task_data:
                    result = task_data['result'].copy()
                    
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'task_active': True,
                        'matched_task': True,
                        'multi_call': False,
                        'text_used': text,
                        'target_language_used': target_language,
                        'source_language_used': source_language
                    }
                    return {
                        'result': result,
                    }
        
        # Fallback to intelligent matching
        # Find best matching task based on parameters
        best_match = find_best_matching_task(text, target_language, source_language)
        
        if best_match:
            task_id, similarity_score = best_match
            result = TASK_DATA[task_id]["result"].copy()
            
            # Add matching information to result (for debugging)
                "method": "similarity_match",
                "matched_task_id": task_id,
                "matched_task": True,
                "multi_call": False,
                "similarity_score": similarity_score,
                "text": text,
                "target_language": target_language,
                "source_language": source_language,
                "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False
            }
            
            return {
                'result': result,
            }
        
        # No match found, return fallback response
        fallback_result = generate_fallback_response(text, target_language, source_language)
        return {
            'result': fallback_result,
                'method': 'default_fallback',
                'matched_task': False,
                'multi_call': False,
                'matched_task_id': None,
                'task_active': task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False
            }
        }
        
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Failed to execute translate_text: {str(e)}",
            "tool": "translate_text"
        }
            "method": "exception_fallback",
            "error": str(e),
            "matched_task": False,
            "multi_call": False,
            "matched_task_id": None,
            "task_active": False
        }

def find_best_matching_task(text: str = None, target_language: str = None, source_language: str = None) -> Optional[tuple]:
    """
    Find the best matching task based on translation parameters
    
    Args:
        text: Text to translate
        target_language: Target language
        source_language: Source language
    
    Returns:
        Tuple of (task_id, similarity_score) or None if no good match
    """
    
    if not TASK_DATA:
        return None
    
    best_match = None
    best_score = 0.0
    
    for task_id, task_data in TASK_DATA.items():
        message_queries = task_data.get("message_queries", [])
        task_target_language = task_data.get("target_language", "")
        task_source_language = task_data.get("source_language", "")
        scenario = task_data.get("scenario", "")
        
        # Calculate base score for this task
        task_score = 0.0
        
        # Message content matching (highest priority - 0.5 weight)
        if text:
            text_lower = text.lower()
            text_words = set(text_lower.split())
            
            # Direct text matches in message queries
            for query in message_queries:
                query_lower = query.lower()
                query_words = set(query_lower.split())
                
                # Exact phrase match
                if query_lower in text_lower or text_lower in query_lower:
                    task_score += 0.5
                    break
                
                # Word overlap matching
                common_words = text_words.intersection(query_words)
                if common_words:
                    overlap_ratio = len(common_words) / max(len(text_words), len(query_words))
                    task_score += overlap_ratio * 0.4
            
            # Special content type matching
            if 'Even monkeys fall from trees' in text and scenario == "japanese_translation":
                task_score += 0.6
            elif 'I-20' in text and scenario == "visa_translation":
                task_score += 0.6
            elif any(char in text for char in ['-', '.', '•']) and scenario == "morse_translation":
                task_score += 0.6
            elif 'fizz cola' in text_lower and scenario == "general_translation":
                task_score += 0.6
        
        # Target language matching (medium priority - 0.3 weight)
        if target_language:
            target_lower = target_language.lower()
            
            # Handle multiple target languages
            if isinstance(task_target_language, list):
                if target_lower in [lang.lower() for lang in task_target_language]:
                    task_score += 0.3
            else:
                if target_lower == task_target_language.lower():
                    task_score += 0.3
        
        # Source language matching (lower priority - 0.2 weight)
        if source_language:
            source_lower = source_language.lower()
            
            if source_lower == task_source_language.lower():
                task_score += 0.2
        
        # Update best match
        if task_score > best_score:
            best_score = task_score
            best_match = (task_id, task_score)
    
    # Return match only if score is above threshold
    if best_score >= 0.3:
        return best_match
    
    return None

def normalize_query(query: str) -> str:
    """
    Normalize query for better matching
    """
    if not query:
        return ""
    
    # Convert to lowercase and remove extra whitespace
    normalized = re.sub(r'\s+', ' ', query.lower().strip())
    
    # Remove common punctuation
    normalized = re.sub(r'[.,!?;:"\']', '', normalized)
    
    return normalized

def generate_fallback_response(text: str = None, target_language: str = None, 
                             source_language: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific match is found
    """
    
    response = DEFAULT_TRANSLATION_RESULT.copy()
    
    # Customize message based on parameters
    if text and target_language:
        response["message"] = f"Successfully translated text to {target_language}"
        response["translated_text"] = f"[Translated to {target_language}]: {text[:50]}..."
    elif text:
        response["message"] = "Text translation completed successfully"
        response["translated_text"] = f"[Translated]: {text[:50]}..."
    elif target_language:
        response["message"] = f"Translation to {target_language} completed"
    else:
        response["message"] = "Translation completed successfully"
        response["translated_text"] = "Translation completed"
    
    # Add random translation ID
    response["translation_id"] = f"TRANS_{random.randint(100000, 999999)}"
    
    return response

# Tool registration schema
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "translate_text",
        "description": "Translate text from one language to another",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to translate"
                },
                "target_language": {
                    "type": "string",
                    "description": "Target language for translation (e.g., 'english', 'spanish', 'chinese')"
                },
                "source_language": {
                    "type": "string",
                    "description": "Source language of the text (optional, auto-detect if not specified)"
                }
            },
            "required": ["text"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="translate_text",
        function=translate_text,
        schema=TOOL_SCHEMA,
        description="Tool function for translate_text"
    )

# Auto-register when module is imported
register_tool()
