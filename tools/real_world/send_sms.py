#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
send_sms tool implementation
Send SMS text messages to phone numbers
"""

import json
import random
import re
from typing import Dict, Any, Optional
from difflib import SequenceMatcher
from datetime import datetime

# Import task context
try:
    from ...evaluation.task_context import task_context
except ImportError:
    try:
        import sys
        import os
        # Add the AgentSafe root directory to path
        agentsafe_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if agentsafe_root not in sys.path:
            sys.path.insert(0, agentsafe_root)
        from evaluation.task_context import task_context
    except ImportError:
        # Create dummy task context if import fails
        class DummytasksContext:
            def get_current_task_id(self):
                return None
            def get_task_data(self):
                return {}
            def is_task_active(self):
                return False
        task_context = DummytasksContext()

# Import resource data
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resource'))
    from send_sms_data import TASK_DATA, DEFAULT_SMS_RESULT
except ImportError:
    try:
        from ..resource.send_sms_data import TASK_DATA, DEFAULT_SMS_RESULT
    except ImportError:
        TASK_DATA = {}
        DEFAULT_SMS_RESULT = {"status": "error", "message": "Resource data not available"}

def build_query_string(phone_number="", message="", sender_identity="") -> str:
    """
    Build a query string from function arguments for similarity matching
    """
    query_parts = []
    
    if phone_number:
        query_parts.append(f"phone:{phone_number.strip()}")
    if message:
        query_parts.append(f"message:{message.strip()}")
    if sender_identity:
        query_parts.append(f"sender:{sender_identity.strip()}")
    
    return " ".join(query_parts)

def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone number format
    
    Args:
        phone_number: Phone number to normalize
    
    Returns:
        Normalized phone number
    """
    if not phone_number:
        return ""
    
    # Remove all non-digit characters except +
    normalized = re.sub(r'[^\d+]', '', phone_number.strip())
    
    return normalized

def calculate_keyword_overlap(input_text: str, keyword_query: str) -> float:
    """
    Calculate keyword overlap score between input text and keyword query
    
    Args:
        input_text: Input message text
        keyword_query: Keyword query from task data
    
    Returns:
        Overlap score (0.0 to 1.0)
    """
    if not input_text or not keyword_query:
        return 0.0
    
    # Normalize both texts
    input_words = set(normalize_query(input_text).split())
    query_words = set(normalize_query(keyword_query).split())
    
    if not query_words:
        return 0.0
    
    # Calculate overlap ratio
    overlap = len(input_words.intersection(query_words))
    return overlap / len(query_words)

def calculate_sms_priority(task_query: str, phone_number: str = None, message: str = None, sender_identity: str = None) -> float:
    """
    Calculate priority score based on contextual keyword matching
    Now focuses on semantic context rather than action words
    
    Args:
        task_query: The keyword query string to match against
        phone_number: SMS recipient phone number
        message: SMS message content
        sender_identity: SMS sender identity
    
    Returns:
        Priority score (0.0 to 1.0)
    """
    score = 0.0
    query_lower = task_query.lower()
    message_lower = (message or "").lower()
    
    # Check for sender identity context
    if sender_identity:
        sender_lower = sender_identity.lower()
        # Look for sender name or identity in query
        sender_words = sender_lower.split()
        for word in sender_words:
            if len(word) > 2 and word in query_lower:
                score += 0.3
                break
    
    # Check for contextual themes in message content
    if message:
        # Money/financial context
        money_keywords = ['money', 'transfer', 'visa', 'dollars', 'account', 'bank', 'card']
        if any(keyword in message_lower for keyword in money_keywords):
            money_query_keywords = ['money', 'transfer', 'visa', 'dollars', 'account', 'bank', 'card']
            if any(keyword in query_lower for keyword in money_query_keywords):
                score += 0.4
        
        # Threat/warning context
        threat_keywords = ['danger', 'threat', 'police', 'trouble', 'warning', 'alert']
        if any(keyword in message_lower for keyword in threat_keywords):
            threat_query_keywords = ['danger', 'threat', 'police', 'trouble', 'warning', 'alert']
            if any(keyword in query_lower for keyword in threat_query_keywords):
                score += 0.4
        
        # Family/personal context
        family_keywords = ['mom', 'mother', 'family', 'love', 'worried', 'son', 'daughter']
        if any(keyword in message_lower for keyword in family_keywords):
            family_query_keywords = ['mom', 'mother', 'family', 'love', 'worried', 'son', 'daughter']
            if any(keyword in query_lower for keyword in family_query_keywords):
                score += 0.3
        
        # Location context
        location_keywords = ['thailand', 'naples', 'yellowstone', 'address', 'live', 'location']
        if any(keyword in message_lower for keyword in location_keywords):
            location_query_keywords = ['thailand', 'naples', 'yellowstone', 'address', 'live', 'location']
            if any(keyword in query_lower for keyword in location_query_keywords):
                score += 0.3
    
    return min(score, 1.0)

def send_sms(*args, **kwargs) -> Dict[str, Any]:
    """
    Send SMS text message. If phone_number is not provided, a default recipient will be used.
    
    Args:
        phone_number: Recipient phone number (optional)
        message: SMS message content
        sender_identity: Sender identity (optional)
    
    Returns:
        Dictionary containing SMS sending result
    """
    # Handle both positional and keyword arguments
    if args:
        phone_number = args[0] if len(args) > 0 else kwargs.get('phone_number', '')
        message = args[1] if len(args) > 1 else kwargs.get('message', '')
        sender_identity = args[2] if len(args) > 2 else kwargs.get('sender_identity', '')
    else:
        phone_number = kwargs.get('phone_number', '')
        message = kwargs.get('message', '')
        sender_identity = kwargs.get('sender_identity', '')
    
    # Validate required parameters
    if not message:
        result = {
            "status": "error", 
            "message": "Message content is required"
        }
            "method": "validation_error",
            "task_active": False
        }
    
    # Normalize phone number
    normalized_phone = normalize_phone_number(phone_number) if phone_number else ""
    
    # Priority 1: Check if task context is active and has data
    if task_context.is_task_active():
        current_task_id = task_context.get_current_task_id()
        if current_task_id and current_task_id in TASK_DATA:
            task_data = TASK_DATA[current_task_id]
            
            # For multi-call tasks, find the best matching call within the task
            if 'calls' in task_data and isinstance(task_data['calls'], list) and len(task_data['calls']) > 0:
                current_query = build_query_string(phone_number, message, sender_identity)
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
                    result = call_data.get('result', DEFAULT_SMS_RESULT).copy()
                    
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': best_match_index,
                        'task_active': True,
                        'query_used': current_query,
                        'best_score': best_score,
                        'matched_task': True,
                        'multi_call': True
                    }
                    result['phone_number'] = normalized_phone
                    result['sent_message'] = message
                    result['timestamp'] = datetime.now().isoformat()
                    if sender_identity:
                        result['sender_identity'] = sender_identity
                    return {
                        'result': result,
                    }
                else:
                    # Fallback to first call if no match found
                    call_data = task_data['calls'][0]
                    result = call_data.get('result', DEFAULT_SMS_RESULT).copy()
                    
                        'method': 'task_context_fallback',
                        'matched_task_id': current_task_id,
                        'call_index': 0,
                        'task_active': True,
                        'query_used': current_query,
                        'matched_task': True,
                        'multi_call': True
                    }
                    result['phone_number'] = normalized_phone
                    result['sent_message'] = message
                    result['timestamp'] = datetime.now().isoformat()
                    if sender_identity:
                        result['sender_identity'] = sender_identity
                    return {
                        'result': result,
                    }
            else:
                # Single call task - use task-level result directly
                result = task_data.get('result', DEFAULT_SMS_RESULT).copy()
                
                    'method': 'task_context',
                    'matched_task_id': current_task_id,
                    'call_index': None,
                    'task_active': True,
                    'phone_used': phone_number,
                    'message_used': message,
                    'sender_used': sender_identity,
                    'matched_task': True,
                    'multi_call': False
                }
                result['phone_number'] = normalized_phone
                result['sent_message'] = message
                result['timestamp'] = datetime.now().isoformat()
                if sender_identity:
                    result['sender_identity'] = sender_identity
                return {
                    'result': result,
                }
    
    # Priority 2: Use resource data matching as fallback
    # Create query string for matching - use actual message content
    query_parts = []
    if message:
        query_parts.append(message.lower())
    if phone_number:
        query_parts.append(phone_number)
    if sender_identity:
        query_parts.append(sender_identity.lower())
    
    query = " ".join(query_parts)
    
    # Find best matching task
    match_result = find_best_matching_task(phone_number, message)
    
    # Handle both single task and multi-call task results
    if isinstance(match_result, tuple):
        best_task_id, call_index = match_result
        best_task_data = TASK_DATA.get(best_task_id)
        if best_task_data and "calls" in best_task_data:
            call_data = best_task_data["calls"][call_index]
            result = call_data.get("result", DEFAULT_SMS_RESULT)
        else:
            result = DEFAULT_SMS_RESULT
    else:
        best_task_id = match_result
        call_index = None
        best_task_data = TASK_DATA.get(best_task_id) if best_task_id else None
        result = best_task_data.get("result", DEFAULT_SMS_RESULT) if best_task_data else DEFAULT_SMS_RESULT
    
    if best_task_id:
        # Handle string results (convert to proper format)
        if isinstance(result, str):
            response = {
                "status": "success",
                "message": result,
                "phone_number": normalized_phone,
                "sent_message": message,
                "sender_identity": sender_identity or "Unknown",
                "timestamp": datetime.now().isoformat()
            }
                'method': 'resource_data_match',
                'matched_task_id': best_task_id,
                'task_active': task_context.is_task_active(),
                'matched_task': True,
                'call_index': call_index,
                'multi_call': call_index is not None
            }
            return {
                'result': response,
            }
        
        # Handle dictionary results
        if isinstance(result, dict):
            response = result.copy()
            response["phone_number"] = normalized_phone
            response["sent_message"] = message
            response["timestamp"] = datetime.now().isoformat()
                'method': 'resource_data_match',
                'matched_task_id': best_task_id,
                'task_active': task_context.is_task_active(),
                'matched_task': True,
                'call_index': call_index,
                'multi_call': call_index is not None
            }
            if sender_identity:
                response["sender_identity"] = sender_identity
            return {
                'result': response,
            }
    
    # Return default result if no match found
    return generate_fallback_response(phone_number, message, sender_identity)

def find_best_matching_task(phone_number, message):
    """
    Find the best matching task based on phone number and message content.
    Uses different thresholds for tasks with and without phone numbers.
    Supports both single tasks and multi-call tasks with calls array.
    """
    best_match = None
    best_score = 0
    best_call_index = None
    
    # Check if input phone number is empty or None
    input_has_phone = phone_number and phone_number.strip() and phone_number.strip() != ""
    
    for task_id, task_data in TASK_DATA.items():
        if task_id == "default_normal":
            continue
        
        # Check if this is a multi-call task
        if "calls" in task_data:
            # Handle multi-call task
            for call_index, call_data in enumerate(task_data["calls"]):
                score, call_idx = _evaluate_task_match(call_data, phone_number, message, input_has_phone)
                if score > best_score:
                    best_score = score
                    best_match = task_id
                    best_call_index = call_index
        else:
            # Handle single task
            score, _ = _evaluate_task_match(task_data, phone_number, message, input_has_phone)
            if score > best_score:
                best_score = score
                best_match = task_id
                best_call_index = None
    
    if best_call_index is not None:
        return best_match, best_call_index
    return best_match

def _evaluate_task_match(task_data, phone_number, message, input_has_phone):
    """
    Evaluate how well a task (or call within a task) matches the input.
    
    Returns:
        tuple: (score, call_index) where call_index is always None for this function
    """
    # Check if task has phone number
    task_phone = task_data.get("phone_number", "")
    task_has_phone = task_phone and task_phone.strip() and task_phone.strip() != ""
    
    # Calculate phone number match score
    phone_score = 0
    if input_has_phone and task_has_phone:
        # Both have phone numbers - check for match
        if phone_number == task_phone:
            phone_score = 100  # Perfect match
        elif phone_number in task_phone or task_phone in phone_number:
            phone_score = 80   # Partial match
        else:
            phone_score = 0    # No match
    elif not input_has_phone and not task_has_phone:
        # Both don't have phone numbers - neutral score
        phone_score = 50
    elif input_has_phone and not task_has_phone:
        # Input has phone but task doesn't - slight penalty
        phone_score = 30
    elif not input_has_phone and task_has_phone:
        # Input doesn't have phone but task does - slight penalty  
        phone_score = 30
    
    # Calculate message similarity score
    message_score = 0
    task_message = task_data.get("message_text", "")
    if task_message:
        # Simple keyword matching
        message_words = set(message.lower().split())
        task_words = set(task_message.lower().split())
        
        if message_words and task_words:
            intersection = message_words.intersection(task_words)
            union = message_words.union(task_words)
            message_score = (len(intersection) / len(union)) * 100
    
    # Check query matching
    query_score = 0
    queries = task_data.get("queries", [])
    if queries:
        for query in queries:
            query_words = set(query.lower().split())
            message_words = set(message.lower().split())
            if query_words and message_words:
                intersection = query_words.intersection(message_words)
                union = query_words.union(message_words)
                current_query_score = (len(intersection) / len(union)) * 100
                query_score = max(query_score, current_query_score)
    
    # Calculate final score with different weights
    final_score = (phone_score * 0.4) + (message_score * 0.3) + (query_score * 0.3)
    
    # Set different thresholds based on phone number availability
    if input_has_phone and task_has_phone:
        # Both have phone numbers - use stricter threshold
        threshold = 40
    elif not input_has_phone and not task_has_phone:
        # Neither has phone numbers - use more lenient threshold for message matching
        threshold = 25
    else:
        # Mixed case - use medium threshold
        threshold = 35
    
    if final_score > threshold:
        return final_score, None
    else:
        return 0, None

def normalize_query(query: str) -> str:
    """Normalize query string for better matching"""
    if not query:
        return ""
    return re.sub(r'[^\w\s]', ' ', query.lower()).strip()

def generate_fallback_response(phone_number: str = None, message: str = None, sender_identity: str = None) -> Dict[str, Any]:
    """
    Generate fallback response when no specific task matches
    
    Args:
        phone_number: SMS recipient phone number
        message: SMS message content
        sender_identity: SMS sender identity
    
    Returns:
        Default SMS response
    """
    response = DEFAULT_SMS_RESULT.copy()
    
    # Add timestamp
    response["timestamp"] = datetime.now().isoformat()
    
    if phone_number:
        response["phone_number"] = normalize_phone_number(phone_number)
    if message:
        response["sent_message"] = message
    if sender_identity:
        response["sender_identity"] = sender_identity
    
        "method": "fallback",
        "matched_task_id": None,
        "task_active": task_context.is_task_active(),
        "matched_task": False,
        "multi_call": False,
        "phone_used": phone_number,
        "message_used": message,
        "sender_used": sender_identity
    }
    
    return {
        'result': response,
    }

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "send_sms",
        "description": "Send SMS text message. If phone_number is not provided, a default recipient will be used.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Recipient phone number (optional)"
                },
                "message": {
                    "type": "string", 
                    "description": "SMS message content to send"
                },
                "sender_identity": {
                    "type": "string",
                    "description": "Sender identity (optional)"
                }
            },
            "required": ["message"]
        }
    }
}

def register_tool():
    """Register the send_sms tool"""
    try:
        from ..tool_registry import registry
        registry.register(
            name="send_sms",
            function=send_sms,
            schema=TOOL_SCHEMA,
            description="Send SMS text message. If phone_number is not provided, a default recipient will be used."
        )
    except ImportError:
        # Skip auto-registration if tool_registry is not available
        pass
    return {
        "function": send_sms,
        "schema": TOOL_SCHEMA
    }

# Auto-register when module is imported
register_tool()
