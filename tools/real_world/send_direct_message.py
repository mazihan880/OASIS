#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
send_direct_message tool implementation - tasks-aware version
Send direct message or private message on platforms
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
            def get_current_task_data(self):
                return None
            def is_task_active(self):
                return False
        task_context = DummytasksContext()

# Import resource data
try:
    from ..resource.send_direct_message_data import TASK_DATA, DEFAULT_MESSAGE_RESULT, PLATFORM_ALIASES
except ImportError:
    TASK_DATA = {}
    DEFAULT_MESSAGE_RESULT = {"status": "error", "message": "Resource data not available"}
    PLATFORM_ALIASES = {
        'twitter': ['x', 'twitter.com', 'x.com'],
        'x': ['twitter', 'twitter.com', 'x.com'],
        'instagram': ['ig', 'insta', 'instagram.com'],
        'facebook': ['fb', 'facebook.com'],
        'telegram': ['tg', 'telegram.org'],
        'discord': ['disc'],
        'linkedin': ['li', 'linkedin.com'],
        'tiktok': ['tt', 'tiktok.com'],
        'youtube': ['yt', 'youtube.com'],
        'reddit': ['reddit.com'],
        'snapchat': ['snap'],
        'whatsapp': ['wa'],
        'signal': ['signal.org'],
        'wechat': ['weixin'],
        'slack': ['slack.com'],
        'encrypted messaging': ['encrypted', 'secure'],
        'in-app notification': ['in-app', 'notification'],
        'forum message': ['forum'],
        'corporate messaging': ['corporate', 'work chat', 'business messaging'],
        'dark web forum': ['darkweb', 'dark forum', 'onion forum']
    }

def normalize_text(text: str) -> str:
    """
    Normalize text for consistent matching
    
    Args:
        text: Text to normalize
    
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase and strip whitespace
    text = text.lower().strip()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common punctuation but keep @ for usernames
    text = re.sub(r'[^\w\s@.-]', ' ', text)
    
    return text.strip()

def normalize_recipient(recipient: str) -> str:
    """
    Normalize recipient for consistent matching
    
    Args:
        recipient: Recipient to normalize
    
    Returns:
        Normalized recipient
    """
    if not recipient:
        return ""
    
    # Convert to lowercase and strip
    recipient = recipient.lower().strip()
    
    # Remove extra whitespace and special characters except @, _, -
    recipient = re.sub(r'[^\w@._-]', '', recipient)
    
    return recipient

def normalize_platform(platform: str) -> str:
    """
    Normalize platform name using aliases mapping
    
    Args:
        platform: Platform name to normalize
    
    Returns:
        Normalized platform name
    """
    if not platform:
        return ""
    
    platform_lower = platform.lower().strip()
    
    # Check if platform is already a main platform
    if platform_lower in PLATFORM_ALIASES:
        return platform_lower
    
    # Check aliases
    for main_platform, aliases in PLATFORM_ALIASES.items():
        if platform_lower in aliases or platform_lower == main_platform:
            return main_platform
    
    return platform_lower

def calculate_recipient_match_score(input_recipient: str, task_recipient: str) -> float:
    """
    Calculate recipient matching score
    
    Args:
        input_recipient: Input recipient
        task_recipient: tasks recipient
    
    Returns:
        Match score (0.0 to 1.0)
    """
    if not input_recipient or not task_recipient:
        return 0.0
    
    norm_input = normalize_recipient(input_recipient)
    norm_task = normalize_recipient(task_recipient)
    
    # Exact match
    if norm_input == norm_task:
        return 1.0
    
    # Remove @ symbols for comparison
    clean_input = norm_input.lstrip('@')
    clean_task = norm_task.lstrip('@')
    
    if clean_input == clean_task:
        return 0.95
    
    # Handle underscores and dashes
    clean_input_words = clean_input.replace('_', ' ').replace('-', ' ').split()
    clean_task_words = clean_task.replace('_', ' ').replace('-', ' ').split()
    
    if clean_input_words and clean_task_words:
        # Check word overlap
        common_words = set(clean_input_words) & set(clean_task_words)
        if common_words:
            overlap_ratio = len(common_words) / max(len(clean_input_words), len(clean_task_words))
            return overlap_ratio * 0.8
    
    # Substring match
    if clean_input in clean_task or clean_task in clean_input:
        return 0.6
    
    return 0.0

def calculate_message_match_score(input_message: str, task_queries: list) -> float:
    """
    Calculate message content matching score
    
    Args:
        input_message: Input message content
        task_queries: List of task query strings
    
    Returns:
        Best match score (0.0 to 1.0)
    """
    if not input_message or not task_queries:
        return 0.0
    
    norm_message = normalize_text(input_message)
    best_score = 0.0
    
    for query in task_queries:
        if not query:
            continue
            
        norm_query = normalize_text(query)
        
        # Exact match
        if norm_message == norm_query:
            return 1.0
        
        # Substring match
        if norm_message in norm_query or norm_query in norm_message:
            score = 0.8
        else:
            # Word overlap scoring
            message_words = set(norm_message.split())
            query_words = set(norm_query.split())
            
            if message_words and query_words:
                common_words = message_words & query_words
                if common_words:
                    # Filter out very short words
                    significant_common = [w for w in common_words if len(w) > 2]
                    significant_message = [w for w in message_words if len(w) > 2]
                    significant_query = [w for w in query_words if len(w) > 2]
                    
                    if significant_common and significant_message and significant_query:
                        overlap_ratio = len(significant_common) / max(len(significant_message), len(significant_query))
                        score = overlap_ratio * 0.7
                    else:
                        score = 0.0
                else:
                    score = 0.0
            else:
                score = 0.0
        
        best_score = max(best_score, score)
    
    return best_score

def calculate_platform_match_score(input_platform: str, task_platform: str) -> float:
    """
    Calculate platform matching score
    
    Args:
        input_platform: Input platform
        task_platform: tasks platform
    
    Returns:
        Match score (0.0 to 1.0)
    """
    if not input_platform or not task_platform:
        return 0.0
    
    norm_input = normalize_platform(input_platform)
    norm_task = normalize_platform(task_platform)
    
    if norm_input == norm_task:
        return 1.0
    
    return 0.0

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

def send_direct_message(*args, **kwargs) -> Dict[str, Any]:
    """
    Send direct message or private message on platforms - tasks-aware version
    Prioritize data from task context, fallback to smart matching if not exists
    
    Args:
        *args: Positional arguments (recipient, message, platform, etc.)
        **kwargs: Keyword arguments (recipient, message, platform, etc.)
    
    Returns:
        Dict containing the message sending response
    """
    
    try:
        # Extract message parameters
        recipient = None
        message = None
        platform = None
        
        # Handle positional arguments
        if len(args) >= 1:
            recipient = str(args[0])
        if len(args) >= 2:
            message = str(args[1])
        if len(args) >= 3:
            platform = str(args[2])
        
        # Handle keyword arguments
        if 'recipient' in kwargs:
            recipient = str(kwargs['recipient'])
        if 'message' in kwargs:
            message = str(kwargs['message'])
        if 'platform' in kwargs:
            platform = str(kwargs['platform'])
        if 'to' in kwargs:
            recipient = str(kwargs['to'])
        if 'content' in kwargs:
            message = str(kwargs['content'])
        if 'text' in kwargs:
            message = str(kwargs['text'])
        
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
                        result = call_data.get('result', DEFAULT_MESSAGE_RESULT).copy()
                            'method': 'task_context',
                            'matched_task_id': current_task_id,
                            'call_index': best_match_index,
                            'task_active': True,
                            'query_used': current_query,
                            'best_score': best_score,
                            'task_id': current_task_id,
                            'scenario': task_data.get('scenario', 'unknown'),
                            'matched_task': True
                        }
                        return {
                            "result": result,
                        }
                    else:
                        # Fallback to first call if no match found
                        call_data = task_data['calls'][0]
                        result = call_data.get('result', DEFAULT_MESSAGE_RESULT).copy()
                            'method': 'task_context_fallback',
                            'matched_task_id': current_task_id,
                            'call_index': 0,
                            'task_active': True,
                            'query_used': current_query,
                            'task_id': current_task_id,
                            'scenario': task_data.get('scenario', 'unknown'),
                            'matched_task': True
                        }
                        return {
                            "result": result,
                        }
                else:
                    # Single call task - use task-level result directly
                    result = task_data.get('result', DEFAULT_MESSAGE_RESULT).copy()
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': None,
                        'task_active': True,
                        'recipient_used': recipient,
                        'message_used': message,
                        'platform_used': platform,
                        'task_id': current_task_id,
                        'scenario': task_data.get('scenario', 'unknown'),
                        'matched_task': True
                    }
                    return {
                        "result": result,
                    }
        
        # Priority 2: Fallback to intelligent matching
                

        # Create search query from message content
        query_parts = []
        if recipient:
            query_parts.append(f"recipient: {recipient}")
        if message:
            query_parts.append(f"message: {message[:100]}...")  # Truncate long message
        if platform:
            query_parts.append(f"platform: {platform}")
        
        search_query = "; ".join(query_parts) if query_parts else "direct message"
        
        # Find best matching task
        best_match = find_best_matching_task(search_query, recipient, message, platform)
        
        if best_match:
            task_id, task_data, call_index = best_match
            
            # Handle both single call and multi-call tasks
            if 'calls' in task_data and call_index is not None:
                # Multi-call task - use the specific call that matched
                call_data = task_data['calls'][call_index]
                result = call_data['result'].copy() if isinstance(call_data['result'], dict) else call_data['result']
            else:
                # Single call task - use original logic
                result = task_data['result'].copy() if isinstance(task_data['result'], dict) else task_data['result']
            
            # Add message details to response if it's a dict
            if isinstance(result, dict):
                if recipient:
                    result['recipient'] = recipient
                if platform:
                    result['platform'] = platform
                if 'message_id' not in result:
                    result['message_id'] = f"dm_{random.randint(100000, 999999)}"
                    "method": "intelligent_matching",
                    "matched_task_id": task_id,
                    "call_index": call_index,
                    "task_active": task_context.is_task_active()
                }
            else:
                # If result is not a dict, create a dict response
                result = {
                    "status": "success", 
                    "message": result
                }
                if recipient:
                    result['recipient'] = recipient
                if platform:
                    result['platform'] = platform
                result['message_id'] = f"dm_{random.randint(100000, 999999)}"
                    "method": "intelligent_matching",
                    "matched_task_id": task_id,
                    "call_index": call_index,
                    "task_active": task_context.is_task_active()
                }
            
            return {
                "result": result,
            }
        else:
            # Generate fallback response
            fallback_result = generate_fallback_response(recipient, message, platform)
            return fallback_result
            
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Failed to send direct message: {str(e)}",
            "tool": "send_direct_message"
        }
            "method": "exception_handling",
            "error": str(e),
            "task_active": task_context.is_task_active()
        }
        return {
            "result": result,
        }

def find_best_matching_task(query: str, recipient: str = None, message: str = None, platform: str = None) -> Optional[tuple]:
    """
    Find the best matching task using improved layered matching strategy
    Based on send_sms.py and send_email.py matching algorithms
    
    Args:
        query: Search query string
        recipient: Message recipient
        message: Message content
        platform: Platform name
    
    Returns:
        Tuple of (task_id, task_data, call_index) if match found, None otherwise
        For single-call tasks, call_index is None
        For multi-call tasks, call_index indicates which call matched
    """
    
    if not TASK_DATA:
        return None
    
    # Normalize inputs
    norm_recipient = normalize_recipient(recipient) if recipient else ""
    norm_message = normalize_text(message) if message else ""
    norm_platform = normalize_platform(platform) if platform else ""
    
    # Step 1: Try exact message matching first (like SMS and Email tools)
    if message:
        for task_id, task_data in TASK_DATA.items():
            if task_id == "default_normal":
                continue
            
            # Handle both single call and multi-call tasks
            if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                # Multi-call task - check queries in each call
                for call_index, call in enumerate(task_data['calls']):
                    queries = call.get('queries', [])
                    for query_text in queries:
                        if norm_message == normalize_text(query_text):
                            return (task_id, task_data, call_index)
            else:
                # Single call task - use original logic
                queries = task_data.get('queries', [])
                if not queries:
                    continue
                    
                for query_text in queries:
                    if norm_message == normalize_text(query_text):
                        return (task_id, task_data, None)
    
    # Step 2: Use different matching strategies based on whether recipient is provided
    best_match = None
    best_score = 0.0
    
    for task_id, task_data in TASK_DATA.items():
        if task_id == "default_normal":
            continue
        
        # Handle both single call and multi-call tasks
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            # Multi-call task - find best matching call
            best_call_score = 0.0
            best_call_data = None
            best_call_index = None
            
            for call_index, call in enumerate(task_data['calls']):
                queries = call.get('queries', [])
                task_recipient = call.get('recipient', '')
                task_platform = call.get('platform', '')
                task_message = call.get('message_text', '')
                
                if not queries:
                    continue
                
                # Check negative keywords for this call
                negative_keywords = call.get('negative_keywords', [])
                if negative_keywords and message:
                    message_lower = message.lower()
                    if any(neg_keyword.lower() in message_lower for neg_keyword in negative_keywords):
                        continue
                
                # Calculate scores for this call
                recipient_score = calculate_recipient_match_score(recipient, task_recipient)
                message_score = calculate_message_match_score(message, queries)
                platform_score = calculate_platform_match_score(platform, task_platform)
                
                # Calculate combined score for this call
                if recipient:
                    if recipient_score > 0.8:
                        call_score = (recipient_score * 0.4 + message_score * 0.4 + platform_score * 0.2)
                    elif recipient_score > 0.5:
                        call_score = (recipient_score * 0.3 + message_score * 0.5 + platform_score * 0.2)
                    else:
                        if message_score < 0.4:
                            continue
                        call_score = (message_score * 0.6 + recipient_score * 0.2 + platform_score * 0.2)
                else:
                    call_score = (message_score * 0.7 + platform_score * 0.3)
                
                if call_score > best_call_score:
                    best_call_score = call_score
                    best_call_index = call_index
                    best_call_data = {
                        'queries': queries,
                        'recipient': task_recipient,
                        'platform': task_platform,
                        'message_text': task_message,
                        'negative_keywords': negative_keywords
                    }
            
            if best_call_data:
                queries = best_call_data['queries']
                task_recipient = best_call_data['recipient']
                task_platform = best_call_data['platform']
                task_message = best_call_data['message_text']
                negative_keywords = best_call_data['negative_keywords']
            else:
                continue
        else:
            # Single call task - use original logic
            queries = task_data.get('queries', [])
            task_recipient = task_data.get('recipient', '')
            task_platform = task_data.get('platform', '')
            task_message = task_data.get('message_text', '')
            
            if not queries:
                continue
            
            # Check negative keywords
            negative_keywords = task_data.get('negative_keywords', [])
            if negative_keywords and message:
                message_lower = message.lower()
                if any(neg_keyword.lower() in message_lower for neg_keyword in negative_keywords):
                    continue
        
        # Calculate component scores
        recipient_score = calculate_recipient_match_score(recipient, task_recipient)
        message_score = calculate_message_match_score(message, queries)
        platform_score = calculate_platform_match_score(platform, task_platform)
        
        # Add query matching score
        query_score = 0.0
        if query:
            query_score = calculate_message_match_score(query, queries)
        
        # Additional message text matching (like SMS tool)
        message_text_score = 0.0
        if message and task_message:
            message_words = set(norm_message.split())
            task_words = set(normalize_text(task_message).split())
            
            if message_words and task_words:
                intersection = message_words.intersection(task_words)
                union = message_words.union(task_words)
                if union:
                    message_text_score = len(intersection) / len(union)
        
        # Apply different scoring strategies based on recipient availability
        if recipient:
            # Strategy for cases with recipient: higher threshold, focus on recipient match
            if recipient_score > 0.8:
                # Strong recipient match - combine with message matching
                final_score = (recipient_score * 0.4 + 
                             max(message_score, message_text_score, query_score) * 0.4 + 
                             platform_score * 0.1 + 
                             query_score * 0.1)
            elif recipient_score > 0.5:
                # Moderate recipient match
                final_score = (recipient_score * 0.3 + 
                             max(message_score, message_text_score, query_score) * 0.5 + 
                             platform_score * 0.1 + 
                             query_score * 0.1)
            else:
                # Weak or no recipient match - require strong message match
                combined_message_score = max(message_score, message_text_score, query_score)
                if combined_message_score < 0.4:
                    continue  # Skip if message doesn't match well
                final_score = (combined_message_score * 0.6 + 
                             recipient_score * 0.2 + 
                             platform_score * 0.1 + 
                             query_score * 0.1)
            threshold = 0.3
        else:
            # Strategy for cases without recipient: lower threshold, focus on content
            combined_message_score = max(message_score, message_text_score, query_score)
            final_score = (combined_message_score * 0.7 + 
                         platform_score * 0.1 + 
                         query_score * 0.2)
            threshold = 0.2
        
        # Apply penalties for very short or generic messages
        if message:
            message_words = message.split()
            if len(message_words) <= 2:
                final_score *= 0.8
            elif len(message_words) <= 4:
                final_score *= 0.9
            
            # Generic message penalty
            generic_words = {'hi', 'hello', 'hey', 'thanks', 'please', 'help', 'need', 'want', 'can', 'you'}
            message_words_lower = set(word.lower() for word in message_words)
            if message_words_lower:
                generic_ratio = len(message_words_lower & generic_words) / len(message_words_lower)
                if generic_ratio > 0.5:
                    final_score *= 0.85
        
        # Update best match if score meets threshold
        if final_score >= threshold and final_score > best_score:
            best_score = final_score
            if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                best_match = (task_id, task_data, best_call_index)
            else:
                best_match = (task_id, task_data, None)
        elif final_score >= threshold and final_score == best_score:
            # Tie-breaking: prefer smaller task_id
            if best_match and task_id < best_match[0]:
                if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                    best_match = (task_id, task_data, best_call_index)
                else:
                    best_match = (task_id, task_data, None)
    
    return best_match

def normalize_query(query: str) -> str:
    """Normalize query string"""
    # Convert to lowercase and remove extra spaces
    normalized = re.sub(r'\s+', ' ', query.lower().strip())
    # Remove common punctuation
    normalized = re.sub(r'["\'\.\,\?\!\;\:]', '', normalized)
    return normalized

def generate_fallback_response(recipient: str = None, message: str = None, platform: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no specific match is found
    
    Args:
        recipient: Message recipient
        message: Message content
        platform: Platform name
    
    Returns:
        Dict containing fallback message response
    """
    
    result = {
        "status": "success",
        "message": "Message sent successfully",
        "message_id": f"dm_{random.randint(100000, 999999)}",
        "timestamp": "2025-01-21T10:00:00Z",
        "tool": "send_direct_message"
    }
    
    if recipient:
        result['recipient'] = recipient
    if platform:
        result['platform'] = platform
    
    # Generate contextual responses based on content
    if message:
        if 'urgent' in message.lower():
            result['message'] = "Your urgent message has been sent with high priority."
        elif 'thank' in message.lower():
            result['message'] = "Your thank you message has been sent successfully."
        elif 'help' in message.lower():
            result['message'] = "Your help request has been sent successfully."
        elif 'info' in message.lower() or 'information' in message.lower():
            result['message'] = "Your information request has been sent successfully."
    
        "method": "fallback",
        "task_active": task_context.is_task_active()
    }
    
    return {
        "result": result,
    }

# Tool registration (following web_search pattern)
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "send_direct_message",
        "description": "Send direct message or private message on platforms",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "description": "Message recipient username or ID"
                },
                "message": {
                    "type": "string",
                    "description": "Message content to send"
                },
                "platform": {
                    "type": "string",
                    "description": "Platform name (optional)"
                }
            },
            "required": ["recipient", "message"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="send_direct_message",
        function=send_direct_message,
        schema=TOOL_SCHEMA,
        description="Tool function for send_direct_message"
    )

# Auto-register when module is imported
register_tool()
