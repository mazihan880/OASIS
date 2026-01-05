#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send Email Tool - Enhanced with robust matching logic
Improved email sending functionality with multi-dimensional scoring
"""

import re
import json
from typing import Dict, Any, List, Tuple, Optional
from difflib import SequenceMatcher
from tools.resource.send_email_data import TASK_DATA, DEFAULT_EMAIL_RESULT

def normalize_email(email: str) -> str:
    """
    Normalize email address for comparison
    
    Args:
        email: Email address to normalize
    
    Returns:
        Normalized email address
    """
    if not email:
        return ""
    
    # Convert to lowercase and strip whitespace
    email = email.lower().strip()
    
    # Remove common email variations
    email = re.sub(r'\s+', '', email)  # Remove all whitespace
    
    return email

def normalize_text(text: str) -> str:
    """
    Normalize text for comparison
    
    Args:
        text: Text to normalize
    
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase and normalize whitespace
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common punctuation for better matching
    text = re.sub(r'[^\w\s@.-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def calculate_keyword_overlap(text1: str, text2: str) -> float:
    """
    Calculate keyword overlap score between two texts
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Overlap score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    norm_text1 = normalize_text(text1)
    norm_text2 = normalize_text(text2)
    
    # Split into words
    words1 = set(norm_text1.split())
    words2 = set(norm_text2.split())
    
    # Remove very short words (less than 3 characters)
    words1 = {w for w in words1 if len(w) >= 3}
    words2 = {w for w in words2 if len(w) >= 3}
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate text similarity using sequence matching
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    norm_text1 = normalize_text(text1)
    norm_text2 = normalize_text(text2)
    
    # Use SequenceMatcher for similarity
    return SequenceMatcher(None, norm_text1, norm_text2).ratio()

def calculate_email_priority(task_data: Dict[str, Any]) -> float:
    """
    Calculate priority score for email task
    
    Args:
        task_data: tasks data dictionary
    
    Returns:
        Priority score between 0 and 1
    """
    priority_score = 0.5  # Base score
    
    # Level-based priority
    level = task_data.get('level', 'L0')
    if level == 'L0':
        priority_score += 0.1
    elif level == 'L1':
        priority_score += 0.2
    elif level == 'L2':
        priority_score += 0.3
    elif level == 'L3':
        priority_score += 0.4
    
    # Difficulty-based priority
    difficulty = task_data.get('difficulty', 'normal')
    if difficulty == 'simple':
        priority_score += 0.1
    elif difficulty == 'normal':
        priority_score += 0.2
    elif difficulty == 'complex':
        priority_score += 0.3
    
    # Scenario-based priority adjustments
    scenario = task_data.get('scenario', '')
    high_priority_scenarios = ['refund_dispute', 'security_report', 'ethics_report']
    if scenario in high_priority_scenarios:
        priority_score += 0.1
    
    return min(priority_score, 1.0)

def build_query_string(recipient="", subject="", message="", sender="") -> str:
    """
    Build a query string from function arguments for similarity matching
    """
    query_parts = []
    
    if recipient:
        query_parts.append(f"recipient:{recipient.strip()}")
    if subject:
        query_parts.append(f"subject:{subject.strip()}")
    if message:
        query_parts.append(f"message:{message.strip()}")
    if sender:
        query_parts.append(f"sender:{sender.strip()}")
    
    return " ".join(query_parts)

def send_email(recipient: str = "", subject: str = "", message: str = "", sender: str = "") -> Dict[str, Any]:
    """
    Send an email to a specified recipient with subject and message content. 
    If recipient is not provided, a default recipient will be used.
    
    Args:
        recipient: Email recipient address (optional)
        subject: Email subject line
        message: Email message content
        sender: Email sender address (optional)
    
    Returns:
        Email sending result
    """
    # Validate required parameters
    if not message:
        result = {
            "status": "error", 
            "message": "Message content is required"
        }
            "method": "validation_error",
            "task_active": False
        }

    # Priority 1: Check if task context is active and has data
    try:
        from ...evaluation.task_context import task_context
        if hasattr(task_context, 'is_task_active') and task_context.is_task_active():
            current_task_id = task_context.get_current_task_id()
            if current_task_id and current_task_id in TASK_DATA:
                task_data = TASK_DATA[current_task_id]
                
                # For multi-call tasks, find the best matching call within the task
                if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                    current_query = build_query_string(recipient, subject, message, sender)
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
                        result = call_data.get('result', DEFAULT_EMAIL_RESULT).copy()
                            'method': 'task_context',
                            'matched_task_id': current_task_id,
                            'call_index': best_match_index,
                            'task_active': True,
                            'multi_call': True,
                            'query_used': current_query,
                            'best_score': best_score,
                            'scenario': task_data.get('scenario', 'unknown')
                        }
                    else:
                        # Fallback to first call if no match found
                        call_data = task_data['calls'][0]
                        result = call_data.get('result', DEFAULT_EMAIL_RESULT).copy()
                            'method': 'task_context_fallback',
                            'matched_task_id': current_task_id,
                            'call_index': 0,
                            'task_active': True,
                            'multi_call': True,
                            'query_used': current_query,
                            'scenario': task_data.get('scenario', 'unknown')
                        }
                else:
                    # Single call task - use task-level result directly
                    result = task_data.get('result', DEFAULT_EMAIL_RESULT).copy()
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': None,
                        'task_active': True,
                        'multi_call': False,
                        'scenario': task_data.get('scenario', 'unknown'),
                        'recipient_used': recipient,
                        'subject_used': subject,
                        'message_used': message,
                        'sender_used': sender
                    }
    except ImportError:
        pass
    
    # Priority 2: Fallback to intelligent matching
    
    # Find best matching task using improved logic (fallback when no task context)
    best_match = find_best_matching_task(recipient, subject, message)
    
    if best_match:
        task_id, call_index = best_match
        if task_id in TASK_DATA:
            task_data = TASK_DATA[task_id]
            
            # Handle both single call and multi-call tasks
            if call_index is not None and 'calls' in task_data:
                # Multi-call task - get result from specific call
                call_data = task_data['calls'][call_index]
                result = call_data.get('result', DEFAULT_EMAIL_RESULT).copy()
            else:
                # Single call task - use task-level result
                result = task_data.get('result', DEFAULT_EMAIL_RESULT).copy()
            
                'method': 'intelligent_matching',
                'matched_task_id': task_id,
                'call_index': call_index,
                'task_active': False,
                'multi_call': call_index is not None,
                'scenario': task_data.get('scenario', 'unknown')
            }
    
    # Return default result if no good match found
    result = generate_fallback_response(recipient, subject, message)
        'method': 'fallback',
        'task_active': False,
        'matched_task': False,
        'fallback': True,
        'recipient_used': recipient,
        'subject_used': subject,
        'message_used': message,
        'sender_used': sender
    }

def find_best_matching_task(recipient: str, subject: str, message: str) -> Optional[tuple]:
    """
    Find the best matching task based on recipient, subject, and message content.
    Uses exact message matching first, then weighted scoring with different strategies
    for cases with and without recipient.
    
    Args:
        recipient: Email recipient address
        subject: Email subject line
        message: Email message content
    
    Returns:
        Tuple of (task_id, call_index) if match found, None otherwise
        For single-call tasks, call_index is None
        For multi-call tasks, call_index indicates which call matched
    """
    # Normalize inputs
    norm_recipient = normalize_email(recipient)
    norm_subject = normalize_text(subject)
    norm_message = normalize_text(message)
    
    # Step 1: Try exact message matching first (like SMS tool)
    for task_id, task_data in TASK_DATA.items():
        # Handle both single call and multi-call tasks
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            # Multi-call task - check queries in each call
            for call_index, call in enumerate(task_data['calls']):
                for query_message in call.get('queries', []):
                    if norm_message == normalize_text(query_message):
                        return (task_id, call_index)
        else:
            # Single call task - use original logic
            for query_message in task_data.get('queries', []):
                if norm_message == normalize_text(query_message):
                    return (task_id, None)
    
    # Step 2: Use different matching strategies based on whether recipient is provided
    best_score = 0
    best_match = None
    
    for task_id, task_data in TASK_DATA.items():
        # Handle both single call and multi-call tasks
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            # Multi-call task - find best matching call
            best_call_score = 0
            best_call_index = None
            
            for call_index, call in enumerate(task_data['calls']):
                if norm_recipient:
                    # Strategy for cases with recipient: higher threshold, focus on recipient match
                    score = calculate_score_with_recipient_for_call(norm_recipient, norm_subject, norm_message, call)
                    threshold = 0.3
                else:
                    # Strategy for cases without recipient: lower threshold, focus on content
                    score = calculate_score_without_recipient_for_call(norm_subject, norm_message, call)
                    threshold = 0.2
                
                if score > best_call_score:
                    best_call_score = score
                    best_call_index = call_index
            
            # Use the best call score for this task
            if best_call_score > best_score:
                best_score = best_call_score
                best_match = (task_id, best_call_index)
        else:
            # Single call task - use original logic
            if norm_recipient:
                # Strategy for cases with recipient: higher threshold, focus on recipient match
                score = calculate_score_with_recipient(norm_recipient, norm_subject, norm_message, task_data)
                threshold = 0.3
            else:
                # Strategy for cases without recipient: lower threshold, focus on content
                score = calculate_score_without_recipient(norm_subject, norm_message, task_data)
                threshold = 0.2
            
            # Update best match if this score is higher
            if score > best_score:
                best_score = score
                best_match = (task_id, None)
    
    # Return best match only if score meets threshold - remove threshold when task context is active
    try:
        from ...evaluation.task_context import task_context
        task_active = hasattr(task_context, 'is_task_active') and task_context.is_task_active()
    except ImportError:
        task_active = False
    
    threshold = 0.0 if task_active else (0.3 if norm_recipient else 0.2)
    if best_score >= threshold:
        return best_match
    
    return None

def calculate_score_with_recipient(recipient: str, subject: str, message: str, task_data: Dict[str, Any]) -> float:
    """Calculate score when recipient is provided - focus on recipient matching"""
    score = 0
    
    # Recipient score (40% weight)
    recipient_score = 0
    task_recipient = task_data.get('recipient', '')
    if task_recipient:
        if recipient == normalize_email(task_recipient):
            recipient_score = 1.0
        elif recipient in normalize_email(task_recipient) or normalize_email(task_recipient) in recipient:
            recipient_score = 0.8
    score += recipient_score * 0.4
    
    # Subject score (30% weight)
    if subject:
        subject_score = 0
        task_subject = task_data.get('subject', '')
        if task_subject:
            norm_task_subject = normalize_text(task_subject)
            if subject == norm_task_subject:
                subject_score = 1.0
            elif subject in norm_task_subject or norm_task_subject in subject:
                subject_score = 0.7
            else:
                overlap = calculate_keyword_overlap(subject, norm_task_subject)
                subject_score = overlap * 0.6
        score += subject_score * 0.3
    
    # Message score (30% weight)
    if message:
        message_score = 0
        for query_message in task_data.get('queries', []):
            norm_query_message = normalize_text(query_message)
            if message in norm_query_message or norm_query_message in message:
                message_score = max(message_score, 0.8)
            else:
                overlap = calculate_keyword_overlap(message, norm_query_message)
                message_score = max(message_score, overlap * 0.7)
        score += message_score * 0.3
    
    return score

def calculate_score_with_recipient_for_call(recipient: str, subject: str, message: str, call_data: Dict[str, Any]) -> float:
    """Calculate score when recipient is provided - focus on recipient matching (for individual call)"""
    score = 0
    
    # Recipient score (40% weight)
    recipient_score = 0
    task_recipient = call_data.get('recipient', '')
    if task_recipient:
        if recipient == normalize_email(task_recipient):
            recipient_score = 1.0
        elif recipient in normalize_email(task_recipient) or normalize_email(task_recipient) in recipient:
            recipient_score = 0.8
    score += recipient_score * 0.4
    
    # Subject score (30% weight)
    if subject:
        subject_score = 0
        task_subject = call_data.get('subject', '')
        if task_subject:
            norm_task_subject = normalize_text(task_subject)
            if subject == norm_task_subject:
                subject_score = 1.0
            elif subject in norm_task_subject or norm_task_subject in subject:
                subject_score = 0.7
            else:
                overlap = calculate_keyword_overlap(subject, norm_task_subject)
                subject_score = overlap * 0.6
        score += subject_score * 0.3
    
    # Message score (30% weight)
    if message:
        message_score = 0
        for query_message in call_data.get('queries', []):
            norm_query_message = normalize_text(query_message)
            if message in norm_query_message or norm_query_message in message:
                message_score = max(message_score, 0.8)
            else:
                overlap = calculate_keyword_overlap(message, norm_query_message)
                message_score = max(message_score, overlap * 0.7)
        score += message_score * 0.3
    
    return score

def calculate_score_without_recipient_for_call(subject: str, message: str, call_data: Dict[str, Any]) -> float:
    """Calculate score when no recipient is provided - focus on content matching (for individual call)"""
    score = 0
    
    # Subject score (50% weight)
    if subject:
        subject_score = 0
        task_subject = call_data.get('subject', '')
        if task_subject:
            norm_task_subject = normalize_text(task_subject)
            if subject == norm_task_subject:
                subject_score = 1.0
            elif subject in norm_task_subject or norm_task_subject in subject:
                subject_score = 0.8
            else:
                overlap = calculate_keyword_overlap(subject, norm_task_subject)
                subject_score = overlap * 0.6
        score += subject_score * 0.5
    
    # Message score (50% weight)
    if message:
        message_score = 0
        for query_message in call_data.get('queries', []):
            norm_query_message = normalize_text(query_message)
            if message in norm_query_message or norm_query_message in message:
                message_score = max(message_score, 0.8)
            else:
                overlap = calculate_keyword_overlap(message, norm_query_message)
                message_score = max(message_score, overlap * 0.7)
        score += message_score * 0.5
    
    return score

def calculate_score_without_recipient(subject: str, message: str, task_data: Dict[str, Any]) -> float:
    """Calculate score when no recipient is provided - focus on content matching"""
    score = 0
    
    # Subject score (50% weight)
    if subject:
        subject_score = 0
        task_subject = task_data.get('subject', '')
        if task_subject:
            norm_task_subject = normalize_text(task_subject)
            if subject == norm_task_subject:
                subject_score = 1.0
            elif subject in norm_task_subject or norm_task_subject in subject:
                subject_score = 0.8
            else:
                overlap = calculate_keyword_overlap(subject, norm_task_subject)
                subject_score = overlap * 0.6
        score += subject_score * 0.5
    
    # Message score (50% weight)
    if message:
        message_score = 0
        for query_message in task_data.get('queries', []):
            norm_query_message = normalize_text(query_message)
            if message in norm_query_message or norm_query_message in message:
                message_score = max(message_score, 0.8)
            else:
                overlap = calculate_keyword_overlap(message, norm_query_message)
                message_score = max(message_score, overlap * 0.7)
        score += message_score * 0.5
    
    return score

def generate_fallback_response(recipient: str, subject: str, message: str) -> Dict[str, Any]:
    """Generate fallback response when no task matches"""
    return {
        "status": "success",
        "message_id": "default_msg_001",
        "to": recipient if recipient else "default@example.com",
        "subject": subject if subject else "Default Subject",
        "body": message
    }

def calculate_recipient_score(input_recipient: str, task_data: Dict[str, Any]) -> float:
    """Calculate recipient matching score"""
    if not input_recipient:
        return 0.0
    
    task_recipient = task_data.get('recipient', '')
    if not task_recipient:
        return 0.0
    
    # Exact match gets highest score
    if normalize_email(input_recipient) == normalize_email(task_recipient):
        return 1.0
    
    # Domain matching
    input_domain = input_recipient.split('@')[-1] if '@' in input_recipient else ''
    task_domain = task_recipient.split('@')[-1] if '@' in task_recipient else ''
    
    if input_domain and task_domain and input_domain.lower() == task_domain.lower():
        return 0.8 # Increased score for domain match
    
    # Partial text similarity and keyword overlap
    similarity = calculate_text_similarity(input_recipient, task_recipient)
    keyword_overlap = calculate_keyword_overlap(input_recipient, task_recipient)

    return (similarity * 0.6 + keyword_overlap * 0.4) * 0.7 # Combined and scaled

def calculate_subject_score(input_subject: str, task_data: Dict[str, Any]) -> float:
    """Calculate subject matching score"""
    if not input_subject:
        return 0.0
    
    task_subject = task_data.get('subject', '')
    if not task_subject:
        return 0.0
    
    # Text similarity
    similarity = calculate_text_similarity(input_subject, task_subject)
    
    # Keyword overlap
    keyword_overlap = calculate_keyword_overlap(input_subject, task_subject)
    
    # Combined score (70% similarity + 30% keyword overlap)
    return similarity * 0.7 + keyword_overlap * 0.3

def calculate_message_score(input_message: str, task_data: Dict[str, Any]) -> float:
    """Calculate message content matching score"""
    if not input_message:
        return 0.0
    
    task_message = task_data.get('message_text', '')
    if not task_message:
        return 0.0
    
    # Text similarity
    similarity = calculate_text_similarity(input_message, task_message)
    
    # Keyword overlap
    keyword_overlap = calculate_keyword_overlap(input_message, task_message)
    
    # Combined score (60% similarity + 40% keyword overlap)
    return similarity * 0.6 + keyword_overlap * 0.4

def calculate_query_score(query: str, task_data: Dict[str, Any]) -> float:
    """Calculate query matching score against task queries"""
    if not query:
        return 0.0
    
    task_queries = task_data.get('queries', [])
    if not task_queries:
        return 0.0
    
    max_score = 0.0
    
    for task_query in task_queries:
        # Check for substring matches
        if normalize_text(task_query) in normalize_text(query) or normalize_text(query) in normalize_text(task_query):
            max_score = max(max_score, 0.9)
        
        # Text similarity
        similarity = calculate_text_similarity(query, task_query)
        max_score = max(max_score, similarity)
        
        # Keyword overlap
        keyword_overlap = calculate_keyword_overlap(query, task_query)
        max_score = max(max_score, keyword_overlap)
    
    return max_score



# Tool schema for the email sending functionality
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": "Send an email to a specified recipient with subject and message content. If recipient is not provided, a default recipient will be used.",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "description": "Email address of the recipient (optional)"
                },
                "subject": {
                    "type": "string", 
                    "description": "Subject line of the email (optional)"
                },
                "message": {
                    "type": "string",
                    "description": "Content/body of the email message"
                },
                "sender": {
                    "type": "string",
                    "description": "Sender email (optional) — if left empty, the current system account will be used to send."
                }
            },
            "required": ["message"]
        }
    }
}


def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="send_email",
        function=send_email,
        schema=TOOL_SCHEMA,
        description="Send an email to a specified recipient"
    )


# Auto-register when module is imported
register_tool()
