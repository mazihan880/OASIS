#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_person_background_info tool implementation - tasks-Aware Version
Search public records and web for personal information
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
    import sys
    import os
    # Add resource directory to path
    resource_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resource')
    if resource_path not in sys.path:
        sys.path.append(resource_path)
    from get_person_background_info_data import TASK_DATA, DEFAULT_BACKGROUND_RESULT
except ImportError:
    TASK_DATA = {}
    DEFAULT_BACKGROUND_RESULT = {
        "status": "success",
        "info": {
            "full_name": "Search completed",
            "age": "Information retrieved",
            "occupation": "Background check finished",
            "education": "Records accessed",
            "contact_info": {
                "status": "Search completed successfully"
            },
            "additional_info": "Background information gathering completed"
        }
    }

def normalize_query(query: str) -> str:
    """
    Normalize query string for better matching
    
    Args:
        query: Query string to normalize
    
    Returns:
        Normalized query string
    """
    if not query:
        return ""
    
    # Convert to lowercase
    normalized = query.lower().strip()
    
    # Remove extra spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove common punctuation but keep @ for email/social handles and & for company names
    normalized = re.sub(r'["\'\.\?\!\;\:]', '', normalized)
    
    # Only remove very generic tokens that truly don't add value
    # Keep professional titles, company terms, and location indicators
    generic_tokens = [
        'information', 'personal', 'background', 'research', 'check', 'records',
        'find', 'search', 'get', 'obtain', 'retrieve', 'lookup', 'details',
        'info', 'data', 'profile', 'biography', 'bio', 'about', 'page',
        'website', 'official', 'headshot', 'photo', 'image', 'picture'
    ]
    
    words = normalized.split()
    filtered_words = [word for word in words if word not in generic_tokens]
    
    return ' '.join(filtered_words) if filtered_words else normalized

def calculate_query_similarity(query1: str, query2: str) -> float:
    """
    Calculate similarity between two queries with enhanced matching
    
    Args:
        query1: First query string
        query2: Second query string
    
    Returns:
        Similarity score (0.0 to 1.0)
    """
    if not query1 or not query2:
        return 0.0
    
    # Normalize both queries
    norm1 = normalize_query(query1)
    norm2 = normalize_query(query2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Calculate sequence similarity
    seq_similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Calculate word overlap
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return seq_similarity
    
    # Basic word overlap
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    word_overlap = len(intersection) / len(union) if union else 0.0
    
    # Enhanced name matching with fuzzy matching
    name_boost = 0.0
    potential_names1 = [w for w in words1 if len(w) > 2 and w.isalpha()]
    potential_names2 = [w for w in words2 if len(w) > 2 and w.isalpha()]
    
    if potential_names1 and potential_names2:
        # Exact name matches
        name_matches = len(set(potential_names1).intersection(set(potential_names2)))
        if name_matches > 0:
            name_boost += min(0.3, name_matches * 0.15)
        
        # Fuzzy name matching for similar names
        for name1 in potential_names1:
            for name2 in potential_names2:
                if len(name1) > 3 and len(name2) > 3:
                    name_sim = SequenceMatcher(None, name1, name2).ratio()
                    if name_sim > 0.8:  # Very similar names
                        name_boost += name_sim * 0.1
    
    # Boost for exact phrase matches
    phrase_boost = 0.0
    if norm1 in norm2 or norm2 in norm1:
        phrase_boost = 0.2
    
    # Boost for partial phrase matches
    partial_boost = 0.0
    words1_str = ' '.join(sorted(words1))
    words2_str = ' '.join(sorted(words2))
    if len(words1_str) > 5 and len(words2_str) > 5:
        partial_sim = SequenceMatcher(None, words1_str, words2_str).ratio()
        if partial_sim > 0.7:
            partial_boost = (partial_sim - 0.7) * 0.3
    
    # Boost for email/social handle matches
    social_boost = 0.0
    if '@' in query1 and '@' in query2:
        handles1 = re.findall(r'@\w+', query1.lower())
        handles2 = re.findall(r'@\w+', query2.lower())
        if handles1 and handles2 and set(handles1).intersection(set(handles2)):
            social_boost = 0.25
    
    # Boost for professional title matches
    title_boost = 0.0
    titles = ['ceo', 'cto', 'cfo', 'director', 'manager', 'president', 'vp', 'vice president', 
              'chief', 'head', 'lead', 'senior', 'partner', 'officer', 'scientist']
    title_words1 = [w for w in words1 if w in titles]
    title_words2 = [w for w in words2 if w in titles]
    if title_words1 and title_words2:
        title_matches = len(set(title_words1).intersection(set(title_words2)))
        if title_matches > 0:
            title_boost = min(0.15, title_matches * 0.1)
    
    # Boost for company/organization matches
    company_boost = 0.0
    company_indicators = ['inc', 'corp', 'llc', 'ltd', 'company', 'corporation', 'solutions', 
                         'systems', 'technologies', 'group', 'associates', 'partners']
    company_words1 = [w for w in words1 if w in company_indicators]
    company_words2 = [w for w in words2 if w in company_indicators]
    if company_words1 and company_words2:
        company_matches = len(set(company_words1).intersection(set(company_words2)))
        if company_matches > 0:
            company_boost = min(0.1, company_matches * 0.05)
    
    # Combine scores with weights
    combined_score = (
        seq_similarity * 0.3 +
        word_overlap * 0.3 +
        name_boost +
        phrase_boost +
        partial_boost +
        social_boost +
        title_boost +
        company_boost
    )
    
    return min(1.0, combined_score)

def get_person_background_info(*args, **kwargs) -> Dict[str, Any]:
    """
    Search public records and web for personal information
    
    Args:
        query: Search query for person information
        
    Returns:
        Dictionary containing background information and metadata
        For common names, returns multiple results for Agent to choose from
    """
    # Extract query from args or kwargs
    if args:
        query = args[0]
    elif 'query' in kwargs:
        query = kwargs['query']
    else:
        return {
            "status": "error",
            "message": "Missing required parameter: query"
        }
    
    # Priority 1: Use task context data if available
    if task_context.is_task_active():
        current_task_id = task_context.get_current_task_id()
        if current_task_id and current_task_id in TASK_DATA:
            task_data = TASK_DATA[current_task_id]
            
            # For multi-call tasks, find the best matching call within the task
            if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
                best_call_index = None
                best_score = -1
                
                # Build query string for matching
                def build_query_string(person_query):
                    return f"get background info for {person_query}"
                
                query_string = build_query_string(query)
                
                for i, call_data in enumerate(task_data['calls']):
                    call_query = call_data.get('query', '')
                    
                    # Try exact query match first
                    if normalize_query(query) == normalize_query(call_query):
                        best_call_index = i
                        best_score = 1.0
                        break
                    
                    # Calculate query similarity using SequenceMatcher
                    call_query_string = build_query_string(call_query)
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
                    result = call_data.get('result', DEFAULT_BACKGROUND_RESULT).copy()
                    
                    # Add query details to response
                    if query:
                        result['query'] = query
                    
                    # Add debug metadata
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': best_call_index,
                        'best_score': best_score,
                        'task_active': True,
                        'matched_task': True,
                        'multi_call': True
                    }
                    return {
                        'result': result,
                    }
            else:
                # Single call task - use task-level result directly
                result = task_data.get('result', DEFAULT_BACKGROUND_RESULT).copy()
                
                # Add query details to response
                if query:
                    result['query'] = query
                
                # Add debug metadata
                    'method': 'task_context',
                    'matched_task_id': current_task_id,
                    'call_index': None,
                    'task_active': True,
                    'matched_task': True,
                    'multi_call': False
                }
                return {
                    'result': result,
                }
    
    # Priority 2: Fallback to intelligent matching
    # Normalize query
    normalized_query = normalize_query(query)
    
    # Find best matching task
    best_match = find_best_matching_task(normalized_query)
    
    if best_match:
        # Check if this is a multi-result response for common names
        if len(best_match) == 3 and best_match[0] == "MULTI_RESULT":
            _, top_score, all_matches = best_match
            
            # Format multiple results for Agent to choose from
            result = {
                "status": "success",
                "multiple_results": True,
                "message": f"Found {len(all_matches)} potential matches for '{query}'. Please review and select the most appropriate one:",
                "candidates": [],
                "_match_info": {
                    "query_type": "common_name",
                    "total_matches": len(all_matches),
                    "original_query": query,
                    "normalized_query": normalized_query,
                    "top_similarity_score": top_score
                }
            }
            
            # Add each candidate with summary info
            for i, (task_id, score, task_data) in enumerate(all_matches[:5]):  # Limit to top 5 results
                candidate_result = task_data["result"].copy()
                
                # Add candidate metadata
                candidate_info = {
                    "candidate_id": i + 1,
                    "task_id": task_id,
                    "similarity_score": score,
                    "summary": {
                        "full_name": candidate_result.get("info", {}).get("full_name", "Unknown"),
                        "occupation": candidate_result.get("info", {}).get("occupation", "Unknown"),
                        "location": candidate_result.get("info", {}).get("address", "Unknown")
                    },
                    "full_details": candidate_result
                }
                
                result["candidates"].append(candidate_info)
            
            return result
        
        # Single result for non-common names
        task_id, similarity_score = best_match
        result = TASK_DATA[task_id]["result"].copy()
        
        # Add debug metadata
            "method": "similarity_match",
            "matched_task_id": task_id,
            "similarity_score": similarity_score,
            "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
            "matched_task": True,
            "multi_call": False
        }
        
        return {
            'result': result,
        }
    
    # No match found, return default result
    result = DEFAULT_BACKGROUND_RESULT.copy()
    
    # Customize default result based on query
    if "name" in normalized_query or any(word in normalized_query for word in ["smith", "miller", "johnson", "brown"]):
        result["info"]["full_name"] = f"Background search completed for query: {query}"
    
        "method": "fallback",
        "task_active": task_context.is_task_active() if hasattr(task_context, 'is_task_active') else False,
        "matched_task": False,
        "multi_call": False,
        "matched_task_id": None
    }
    
    return {
        'result': result,
    }

def calculate_context_similarity(query: str, task_data: Dict[str, Any]) -> float:
    """
    Calculate contextual similarity using task result information
    
    Args:
        query: User query
        task_data: tasks data including result information
    
    Returns:
        Context similarity score (0.0 to 1.0)
    """
    context_score = 0.0
    query_lower = query.lower()
    
    # Extract context from task result
    result_info = task_data.get("result", {}).get("info", {})
    
    # Check for location matches
    addresses = result_info.get("addresses", [])
    for addr in addresses:
        if isinstance(addr, str):
            addr_words = set(addr.lower().split())
            query_words = set(query_lower.split())
            if addr_words.intersection(query_words):
                context_score += 0.2
    
    # Check for employment/company matches
    employment = result_info.get("employment_history", [])
    for emp in employment:
        if isinstance(emp, str) and any(word in emp.lower() for word in query_lower.split()):
            context_score += 0.15
    
    # Check for email/social media matches
    emails = result_info.get("email_addresses", [])
    for email in emails:
        if isinstance(email, str) and email.lower() in query_lower:
            context_score += 0.25
    
    social_media = result_info.get("social_media", {})
    for platform, handle in social_media.items():
        if isinstance(handle, str) and handle.lower() in query_lower:
            context_score += 0.2
    
    # Check for phone number matches
    phones = result_info.get("phone_numbers", [])
    for phone in phones:
        if isinstance(phone, str):
            # Extract digits from both query and phone
            query_digits = re.sub(r'\D', '', query)
            phone_digits = re.sub(r'\D', '', phone)
            if len(query_digits) >= 4 and query_digits in phone_digits:
                context_score += 0.3
    
    return min(1.0, context_score)

def is_common_name_query(query: str) -> bool:
    """
    Detect if query contains common names that might have multiple matches
    Only triggers for simple name queries without additional context
    
    Args:
        query: User query
    
    Returns:
        True if query contains common names without specific context
    """
    common_names = {
        'john smith', 'jane doe', 'john doe', 'jane smith', 'david chen', 'john anderson',
        'michael johnson', 'sarah williams', 'robert brown', 'jennifer davis',
        'michael thompson', 'alex thompson', 'maria flores', 'david kim'
    }
    
    # Context indicators that suggest a specific person
    context_indicators = {
        'cfo', 'ceo', 'manager', 'director', 'engineer', 'developer', 'analyst',
        'professor', 'doctor', 'attorney', 'lawyer', 'consultant', 'specialist',
        'springfield', 'boston', 'chicago', 'seattle', 'denver', 'atlanta',
        'university', 'college', 'company', 'corporation', 'inc', 'llc',
        'bank', 'hospital', 'school', 'department', 'office', 'firm',
        'marketing', 'sales', 'finance', 'accounting', 'hr', 'it', 'tech'
    }
    
    query_lower = normalize_query(query).lower()
    query_words = set(query_lower.split())
    
    # If query contains context indicators, don't use multi-result
    if any(indicator in query_lower for indicator in context_indicators):
        return False
    
    # If query is too long (>4 words), likely has context
    if len(query_words) > 4:
        return False
    
    # Check for exact common name matches in simple queries
    for common_name in common_names:
        common_words = set(common_name.split())
        # Must be exact match or very close (all common name words present)
        if common_words.issubset(query_words) and len(query_words) <= len(common_words) + 1:
            return True
    
    return False

def find_all_matching_tasks(query: str) -> list:
    """
    Find all matching tasks for common name queries
    
    Args:
        query: Normalized query string
    
    Returns:
        List of (task_id, similarity_score, task_data) tuples
    """
    matches = []
    
    # Dynamic threshold - remove threshold when task context is active
    try:
        task_active = hasattr(task_context, 'is_task_active') and task_context.is_task_active()
    except:
        task_active = False
    
    min_threshold = 0.0 if task_active else 0.3
    
    # Extract key information from query
    query_words = set(normalize_query(query).split())
    
    for task_id, task_data in TASK_DATA.items():
        task_best_score = 0.0
        best_query_match = None
        
        for task_query in task_data["queries"]:
            # Calculate base similarity
            similarity = calculate_query_similarity(query, task_query)
            
            # Additional scoring for key term matches
            task_words = set(normalize_query(task_query).split())
            
            if query_words and task_words:
                # Boost for high overlap of meaningful words
                overlap_ratio = len(query_words.intersection(task_words)) / len(query_words.union(task_words))
                if overlap_ratio > 0.5:
                    similarity += overlap_ratio * 0.15
                
                # Boost for name-like word matches
                important_query_words = {w for w in query_words if len(w) > 2}
                important_task_words = {w for w in task_words if len(w) > 2}
                
                if important_query_words and important_task_words:
                    important_overlap = len(important_query_words.intersection(important_task_words))
                    if important_overlap > 0:
                        similarity += (important_overlap / max(len(important_query_words), len(important_task_words))) * 0.1
            
            # Boost for exact query match
            if normalize_query(query) == normalize_query(task_query):
                similarity += 0.3
            
            # Update task best score
            if similarity > task_best_score:
                task_best_score = similarity
                best_query_match = task_query
        
        # Add to matches if above threshold
        if task_best_score >= min_threshold:
            matches.append((task_id, task_best_score, task_data))
    
    # Sort by score (descending)
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches

def find_best_matching_task(query: str) -> Optional[tuple]:
    """
    Find the best matching task with multi-result support for common names
    
    Args:
        query: Normalized query string
    
    Returns:
        (task_id, similarity_score) or None
        For common names, returns multiple results in special format
    """
    # Check if this is a common name query
    if is_common_name_query(query):
        all_matches = find_all_matching_tasks(query)
        if all_matches:
            # Return multiple results for common names
            # Format: ("MULTI_RESULT", score, [list of matches])
            return ("MULTI_RESULT", all_matches[0][1], all_matches)
    
    # Original single-result logic for non-common names
    best_match = None
    best_score = 0.0
    
    # Dynamic threshold - remove threshold when task context is active
    try:
        task_active = hasattr(task_context, 'is_task_active') and task_context.is_task_active()
    except:
        task_active = False
    
    min_threshold = 0.0 if task_active else 0.3
    
    # Extract key information from query
    query_words = set(normalize_query(query).split())
    
    # First pass: collect all candidates with their scores
    candidates = []
    
    for task_id, task_data in TASK_DATA.items():
        task_best_score = 0.0
        best_query_match = None
        
        for task_query in task_data["queries"]:
            # Calculate base similarity
            similarity = calculate_query_similarity(query, task_query)
            
            # Additional scoring for key term matches
            task_words = set(normalize_query(task_query).split())
            
            if query_words and task_words:
                # Boost for high overlap of meaningful words
                overlap_ratio = len(query_words.intersection(task_words)) / len(query_words.union(task_words))
                if overlap_ratio > 0.5:
                    similarity += overlap_ratio * 0.15
                
                # Boost for name-like word matches
                important_query_words = {w for w in query_words if len(w) > 2}
                important_task_words = {w for w in task_words if len(w) > 2}
                
                if important_query_words and important_task_words:
                    important_overlap = len(important_query_words.intersection(important_task_words))
                    if important_overlap > 0:
                        similarity += (important_overlap / max(len(important_query_words), len(important_task_words))) * 0.1
            
            # Boost for exact query match
            if normalize_query(query) == normalize_query(task_query):
                similarity += 0.3
            
            # Update task best score
            if similarity > task_best_score:
                task_best_score = similarity
                best_query_match = task_query
        
        # Add to candidates if above threshold
        if task_best_score >= min_threshold:
            candidates.append((task_id, task_best_score, best_query_match, task_data))
    
    if not candidates:
        return None
    
    # Sort candidates by score (descending)
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Return the best candidate
    return (candidates[0][0], candidates[0][1])

def generate_fallback_response(query: str = None) -> Dict[str, Any]:
    """
    Generate a fallback response when no match is found
    
    Args:
        query: Original query string
    
    Returns:
        Fallback response dictionary
    """
    result = DEFAULT_BACKGROUND_RESULT.copy()
    
    if query:
        result["info"]["additional_info"] = f"Background search completed for: {query}"
    
    return result

# Tool schema for registration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_person_background_info",
        "description": "Search public records and web for personal information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for person information (name, location, etc.)"
                }
            },
            "required": ["query"]
        }
    }
}

def register_tool():
    """Register the tool with the system"""
    from ..tool_registry import registry
    registry.register(
        name="get_person_background_info",
        function=get_person_background_info,
        schema=TOOL_SCHEMA,
        description="Search public records and web for personal information"
    )

# Auto-register when module is imported
register_tool()