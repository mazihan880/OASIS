#!/usr/bin/env python3
"""
Web Search Tool - tasks-Aware Version
Uses task context to load specific resource data for deterministic results
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from difflib import SequenceMatcher
from ..resource.web_search_data import TASK_DATA, DEFAULT_SEARCH_RESULT, get_all_queries

def build_query_string(query="", num_results=5, time_range=None) -> str:
    """
    Build a query string from function arguments for similarity matching
    """
    query_parts = []
    
    if query:
        query_parts.append(f"query:{query.strip()}")
    if num_results != 5:  # Only include if different from default
        query_parts.append(f"num_results:{num_results}")
    if time_range:
        query_parts.append(f"time_range:{time_range.strip()}")
    
    return " ".join(query_parts)

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
        # If unable to import task context, create empty context object
        class DummytasksContext:
            def get_current_task_id(self) -> Optional[str]:
                return None
            def is_task_active(self) -> bool:
                return False
        task_context = DummytasksContext()


def web_search(query: str, num_results: int = 5, time_range: str = None) -> Dict[str, Any]:
    """Execute web search using task-aware resource loading
    
    Args:
        query: Search keywords or question
        num_results: Number of results to return (default: 5)
        time_range: Search time range (e.g., last_day, last_week, last_year)
        
    Returns:
        Dictionary containing search results and metadata
    """
    # Priority 1: Check if task context is active and has data
    current_task_id = task_context.get_current_task_id()
    if current_task_id and task_context.is_task_active() and current_task_id in TASK_DATA:
        task_data = TASK_DATA[current_task_id]
        
        # For multi-call tasks, find the best matching call within the task
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            current_query = build_query_string(query, num_results, time_range)
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
                call_result = call_data.get('result', DEFAULT_SEARCH_RESULT)
                
                return {
                    'result': call_result,
                        'method': 'task_context',
                        'matched_task_id': current_task_id,
                        'call_index': best_match_index,
                        'task_active': True,
                        'query_used': current_query,
                        'best_score': best_score
                    }
                }
            else:
                # Fallback to first call if no match found
                call_data = task_data['calls'][0]
                call_result = call_data.get('result', DEFAULT_SEARCH_RESULT)
                
                return {
                    'result': call_result,
                        'method': 'task_context_fallback',
                        'matched_task_id': current_task_id,
                        'call_index': 0,
                        'task_active': True,
                        'query_used': current_query
                    }
                }
        else:
            # Single call task - use task-level result directly
            if task_data and 'result' in task_data:
                task_result = task_data['result']
                
                return {
                    'result': task_result,
                        'method': 'task_context',
                        'task_id': current_task_id,
                        'task_active': True,
                        'query_used': query,
                        'num_results_used': num_results,
                        'time_range_used': time_range
                    }
                }
    
    # If no task context or task data exists, fallback to smart matching
    normalized_query = normalize_query(query)
    best_match = find_best_matching_task(normalized_query)
    
    if best_match:
        task_id, similarity_score, call_index = best_match
        task_data = TASK_DATA[task_id]
        
        # Handle multi-call tasks with calls array
        if 'calls' in task_data and call_index is not None:
            match_result = task_data['calls'][call_index]['result']
            return {
                "result": match_result,
                    "method": "intelligent_matching",
                    "matched_task_id": task_id,
                    "call_index": call_index,
                    "similarity_score": similarity_score,
                    "task_active": task_context.is_task_active()
                }
            }
        else:
            # Handle legacy single task structure
            match_result = task_data["result"]
            return {
                "result": match_result,
                    "method": "intelligent_matching",
                    "matched_task_id": task_id,
                    "similarity_score": similarity_score,
                    "task_active": task_context.is_task_active()
                }
            }
    
    # No match found, return default result
    fallback_result = DEFAULT_SEARCH_RESULT.copy()
    fallback_result["results"][0]["title"] = f"Search results for: {query}"
    fallback_result["results"][0]["url"] = f"https://search-engine.com/results?q={query.replace(' ', '+')}"
    fallback_result["results"][0]["snippet"] = f"Found relevant information about {query}. Multiple sources available."
    
    return {
        "result": fallback_result,
            "method": "fallback",
            "task_active": task_context.is_task_active()
        }
    }


def normalize_query(query: str) -> str:
    """Normalize query string"""
    # Convert to lowercase
    normalized = query.lower().strip()
    
    # Remove extra spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove common punctuation
    normalized = re.sub(r'["\'\.\,\?\!\;\:]', '', normalized)
    
    # Remove common stop words (optional)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    words = normalized.split()
    filtered_words = [word for word in words if word not in stop_words]
    
    return ' '.join(filtered_words) if filtered_words else normalized


def find_best_matching_task(query: str) -> Tuple[str, float, int] or None:
    """Find the best matching task with enhanced similarity calculation
    Supports both single tasks and multi-call tasks with calls array.
    
    Returns:
        (task_id, similarity_score, call_index) or None
    """
    best_match = None
    best_score = 0.0
    
    # Dynamic threshold based on task context
    if task_context.is_task_active():
        min_threshold = 0.0  # Always return best match when task is active
    else:
        min_threshold = 0.35  # Lowered threshold for better recall
    
    # Track all potential matches for conflict resolution
    potential_matches = []
    
    for task_id, task_data in TASK_DATA.items():
        # Handle new calls array structure for multi-call tasks
        if 'calls' in task_data and len(task_data.get('calls', [])) > 0:
            for call_idx, call_data in enumerate(task_data['calls']):
                task_best_score = 0.0
                task_best_query = None
                task_best_match_type = None
                
                for task_query in call_data.get("queries", []):
                    # Normalize both queries
                    normalized_query = normalize_query(query)
                    normalized_task_query = normalize_query(task_query)
                    
                    # Calculate multiple similarity metrics
                    sequence_sim = SequenceMatcher(None, normalized_query, normalized_task_query).ratio()
                    word_overlap_sim = calculate_word_overlap_similarity(normalized_query, normalized_task_query)
                    substring_sim = calculate_substring_similarity(normalized_query, normalized_task_query)
                    keyword_sim = calculate_keyword_similarity(normalized_query, normalized_task_query)
                    
                    # Add fuzzy matching for better synonym detection
                    fuzzy_sim = calculate_fuzzy_similarity(normalized_query, normalized_task_query)
                    
                    # Determine match type for better conflict resolution
                    match_type = "partial"
                    if sequence_sim > 0.8:
                        match_type = "exact"
                    elif word_overlap_sim > 0.6:
                        match_type = "high_overlap"
                    elif normalized_query in normalized_task_query or normalized_task_query in normalized_query:
                        match_type = "substring"
                    elif fuzzy_sim > 0.7:
                        match_type = "fuzzy_match"
                    
                    # Use adaptive weights based on query characteristics and match type
                    if match_type == "exact":
                        weights = [0.6, 0.2, 0.1, 0.05, 0.05]
                    elif match_type == "high_overlap":
                        weights = [0.3, 0.4, 0.15, 0.1, 0.05]
                    elif len(normalized_query.split()) <= 2:
                        weights = [0.4, 0.3, 0.1, 0.1, 0.1]
                    else:
                        weights = [0.25, 0.25, 0.2, 0.15, 0.15]
                    
                    similarity_scores = [sequence_sim, word_overlap_sim, substring_sim, keyword_sim, fuzzy_sim]
                    final_score = sum(score * weight for score, weight in zip(similarity_scores, weights))
                    
                    # Apply bonuses and penalties
                    if normalized_query in normalized_task_query or normalized_task_query in normalized_query:
                        final_score *= 1.15
                    
                    if word_overlap_sim > 0.7:
                        final_score *= 1.1
                    
                    if len(normalized_query.split()) <= 2 and len(normalized_task_query.split()) > 4:
                        final_score *= 0.8
                    
                    generic_terms = {'photo', 'weather', 'music', 'search', 'find', 'get'}
                    if normalized_query.strip() in generic_terms:
                        final_score *= 0.8
                    
                    # Track best score for this task
                    if final_score > task_best_score:
                        task_best_score = final_score
                        task_best_query = task_query
                        task_best_match_type = match_type
                
                # Only consider this task if it meets the threshold
                if task_best_score >= min_threshold:
                    potential_matches.append((task_id, task_best_score, task_best_query, task_best_match_type, call_idx))
        else:
            # Handle legacy single task structure
            task_best_score = 0.0
            task_best_query = None
            task_best_match_type = None
            
            for task_query in task_data.get("queries", []):
                # Normalize both queries
                normalized_query = normalize_query(query)
                normalized_task_query = normalize_query(task_query)
                
                # Calculate multiple similarity metrics
                sequence_sim = SequenceMatcher(None, normalized_query, normalized_task_query).ratio()
                word_overlap_sim = calculate_word_overlap_similarity(normalized_query, normalized_task_query)
                substring_sim = calculate_substring_similarity(normalized_query, normalized_task_query)
                keyword_sim = calculate_keyword_similarity(normalized_query, normalized_task_query)
                
                # Add fuzzy matching for better synonym detection
                fuzzy_sim = calculate_fuzzy_similarity(normalized_query, normalized_task_query)
                
                # Determine match type for better conflict resolution
                match_type = "partial"
                if sequence_sim > 0.8:
                    match_type = "exact"
                elif word_overlap_sim > 0.6:
                    match_type = "high_overlap"
                elif normalized_query in normalized_task_query or normalized_task_query in normalized_query:
                    match_type = "substring"
                elif fuzzy_sim > 0.7:
                    match_type = "fuzzy_match"
                
                # Use adaptive weights based on query characteristics and match type
                if match_type == "exact":
                    weights = [0.6, 0.2, 0.1, 0.05, 0.05]
                elif match_type == "high_overlap":
                    weights = [0.3, 0.4, 0.15, 0.1, 0.05]
                elif len(normalized_query.split()) <= 2:
                    weights = [0.4, 0.3, 0.1, 0.1, 0.1]
                else:
                    weights = [0.25, 0.25, 0.2, 0.15, 0.15]
                
                similarity_scores = [sequence_sim, word_overlap_sim, substring_sim, keyword_sim, fuzzy_sim]
                final_score = sum(score * weight for score, weight in zip(similarity_scores, weights))
                
                # Apply bonuses and penalties
                if normalized_query in normalized_task_query or normalized_task_query in normalized_query:
                    final_score *= 1.15
                
                if word_overlap_sim > 0.7:
                    final_score *= 1.1
                
                if len(normalized_query.split()) <= 2 and len(normalized_task_query.split()) > 4:
                    final_score *= 0.8
                
                generic_terms = {'photo', 'weather', 'music', 'search', 'find', 'get'}
                if normalized_query.strip() in generic_terms:
                    final_score *= 0.8
                
                # Track best score for this task
                if final_score > task_best_score:
                    task_best_score = final_score
                    task_best_query = task_query
                    task_best_match_type = match_type
            
            # Only consider this task if it meets the threshold
            if task_best_score >= min_threshold:
                potential_matches.append((task_id, task_best_score, task_best_query, task_best_match_type, None))
    
    # Sort by score and apply advanced conflict resolution
    potential_matches.sort(key=lambda x: x[1], reverse=True)
    
    if potential_matches:
        # If there's a clear winner (significantly higher score), use it
        if len(potential_matches) == 1 or potential_matches[0][1] - potential_matches[1][1] > 0.12:
            best_match = (potential_matches[0][0], potential_matches[0][1], potential_matches[0][4])
        else:
            # Advanced conflict resolution for close matches
            best_candidate = resolve_conflicts(query, potential_matches[:3])
            best_match = best_candidate
    
    return best_match


def resolve_conflicts(query: str, candidates: List[Tuple[str, float, str, str, Optional[int]]]) -> Tuple[str, float, Optional[int]] or None:
    """Advanced conflict resolution for close matches"""
    if not candidates:
        return None
    
    # Score each candidate based on multiple factors
    scored_candidates = []
    
    for task_id, score, matched_query, match_type, call_idx in candidates:
        conflict_score = score
        
        # Factor 1: Match type preference (exact > high_overlap > substring > partial)
        type_bonus = {
            "exact": 0.2,
            "high_overlap": 0.1,
            "substring": 0.05,
            "partial": 0.0
        }
        conflict_score += type_bonus.get(match_type, 0.0)
        
        # Factor 2: Query specificity (longer, more specific queries get bonus)
        specificity_score = len(matched_query.split()) / 10.0  # Normalize
        conflict_score += specificity_score * 0.1
        
        # Factor 3: Exact word matches
        query_words = set(query.lower().split())
        matched_words = set(matched_query.lower().split())
        exact_word_matches = len(query_words.intersection(matched_words))
        conflict_score += exact_word_matches * 0.05
        
        # Factor 4: Penalize very generic matches
        if any(generic in matched_query.lower() for generic in ['photo', 'image', 'picture']):
            if query.lower().strip() in ['photo', 'image', 'picture']:
                conflict_score *= 0.5  # Heavy penalty for generic photo queries
        
        scored_candidates.append((task_id, conflict_score, matched_query, call_idx))
    
    # Sort by final conflict resolution score
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Return the best candidate
    return (scored_candidates[0][0], scored_candidates[0][1], scored_candidates[0][3])


def calculate_word_overlap_similarity(query1: str, query2: str) -> float:
    """Calculate word overlap similarity"""
    words1 = set(query1.split())
    words2 = set(query2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


def calculate_substring_similarity(query1: str, query2: str) -> float:
    """Calculate substring matching similarity"""
    # Check if shorter string is a substring of longer string
    shorter, longer = (query1, query2) if len(query1) <= len(query2) else (query2, query1)
    
    if shorter in longer:
        return len(shorter) / len(longer)
    
    # Calculate longest common subsequence
    def lcs_length(s1, s2):
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    lcs_len = lcs_length(query1, query2)
    max_len = max(len(query1), len(query2))
    
    return lcs_len / max_len if max_len > 0 else 0.0


def calculate_keyword_similarity(query1: str, query2: str) -> float:
    """Calculate keyword matching similarity"""
    # Extract keywords (words longer than 2 characters)
    keywords1 = set(word for word in query1.split() if len(word) > 2)
    keywords2 = set(word for word in query2.split() if len(word) > 2)
    
    if not keywords1 or not keywords2:
        return 0.0
    
    # Calculate keyword overlap
    intersection = len(keywords1.intersection(keywords2))
    union = len(keywords1.union(keywords2))
    
    return intersection / union if union > 0 else 0.0


def calculate_fuzzy_similarity(query1: str, query2: str) -> float:
    """Calculate fuzzy similarity using synonym detection and partial matching"""
    words1 = query1.split()
    words2 = query2.split()
    
    if not words1 or not words2:
        return 0.0
    
    # Common synonyms and variations for better matching
    synonyms = {
        'free': ['royalty-free', 'no-cost', 'gratis', 'complimentary'],
        'royalty-free': ['free', 'no-cost', 'copyright-free'],
        'image': ['photo', 'picture', 'pic', 'graphic', 'illustration'],
        'photo': ['image', 'picture', 'pic', 'photograph'],
        'picture': ['photo', 'image', 'pic', 'illustration'],
        'silhouette': ['outline', 'shadow', 'profile', 'shape'],
        'outline': ['silhouette', 'contour', 'shape'],
        'head': ['face', 'portrait', 'headshot'],
        'lion': ['lions', 'big-cat'],
        'graphics': ['images', 'pictures', 'illustrations'],
        'vector': ['svg', 'scalable'],
        'clipart': ['graphics', 'illustrations'],
        'download': ['get', 'obtain', 'access'],
        'best': ['top', 'finest', 'excellent', 'great'],
        'top': ['best', 'finest', 'leading'],
        'restaurant': ['eatery', 'dining', 'bistro'],
        'restaurants': ['eateries', 'dining'],
        'food': ['cuisine', 'dining', 'meal'],
        'weather': ['forecast', 'conditions', 'climate'],
        'forecast': ['weather', 'prediction', 'outlook'],
        'current': ['today', 'now', 'present'],
        'today': ['current', 'now'],
        'music': ['audio', 'sound', 'track'],
        'audio': ['music', 'sound'],
        'biography': ['life', 'profile', 'history'],
        'life': ['biography', 'story'],
        'vintage': ['antique', 'retro', 'classic', 'old-fashioned'],
        'antique': ['vintage', 'classic', 'old'],
        'retro': ['vintage', 'classic'],
        'celestial': ['star', 'astronomical', 'space', 'cosmic'],
        'star': ['celestial', 'stellar'],
        'engagement': ['wedding', 'bridal'],
        'ring': ['rings', 'jewelry'],
        'rings': ['ring', 'jewelry'],
        'movie': ['film', 'cinema'],
        'film': ['movie', 'cinema'],
        'showtimes': ['schedule', 'times', 'showings'],
        'schedule': ['times', 'showtimes'],
        'times': ['schedule', 'showtimes'],
        'lyrics': ['words', 'text', 'song-text'],
        'words': ['lyrics', 'text'],
        'song': ['track', 'music'],
        'news': ['articles', 'reports'],
        'articles': ['news', 'reports'],
        'recent': ['latest', 'new', 'current'],
        'latest': ['recent', 'new', 'current'],
        'used': ['pre-owned', 'second-hand'],
        'pre-owned': ['used', 'second-hand'],
        'second-hand': ['used', 'pre-owned'],
        'car': ['vehicle', 'auto'],
        'vehicle': ['car', 'auto'],
        'logo': ['emblem', 'symbol', 'brand'],
        'emblem': ['logo', 'symbol'],
        'symbol': ['logo', 'emblem'],
        'official': ['authentic', 'genuine'],
        'park': ['parks'],
        'parks': ['park'],
        'national': ['state', 'public'],
        'api': ['interface', 'service'],
        'key': ['token', 'access'],
        'lost': ['ancient', 'forgotten', 'abandoned'],
        'ancient': ['old', 'historic', 'lost'],
        'cities': ['city', 'settlements'],
        'city': ['cities', 'urban'],
        'castle': ['fortress', 'fortification'],
        'fortress': ['castle', 'fort'],
        'architecture': ['design', 'construction'],
        'design': ['architecture', 'style'],
        'medieval': ['middle-ages', 'historic'],
        'tutorial': ['guide', 'instructions', 'help'],
        'guide': ['tutorial', 'instructions'],
        'instructions': ['tutorial', 'guide'],
        'online': ['internet', 'web'],
        'internet': ['online', 'web'],
        'web': ['online', 'internet']
    }
    
    # Calculate fuzzy matches
    matches = 0
    total_comparisons = 0
    
    for word1 in words1:
        word1_lower = word1.lower()
        for word2 in words2:
            word2_lower = word2.lower()
            total_comparisons += 1
            
            # Exact match
            if word1_lower == word2_lower:
                matches += 1
            # Synonym match
            elif word1_lower in synonyms and word2_lower in synonyms[word1_lower]:
                matches += 0.8  # Slightly lower score for synonyms
            elif word2_lower in synonyms and word1_lower in synonyms[word2_lower]:
                matches += 0.8
            # Partial match (one word contains the other)
            elif word1_lower in word2_lower or word2_lower in word1_lower:
                matches += 0.6
            # Similar words (edit distance)
            elif len(word1_lower) > 3 and len(word2_lower) > 3:
                # Simple edit distance check for similar words
                if abs(len(word1_lower) - len(word2_lower)) <= 2:
                    common_chars = len(set(word1_lower) & set(word2_lower))
                    if common_chars >= min(len(word1_lower), len(word2_lower)) * 0.7:
                        matches += 0.4
    
    if total_comparisons == 0:
        return 0.0
    
    # Normalize by the maximum possible matches
    max_possible_matches = min(len(words1), len(words2))
    if max_possible_matches == 0:
        return 0.0
    
    return min(matches / max_possible_matches, 1.0)


def get_query_suggestions(query: str, limit: int = 5) -> List[str]:
    """Get query suggestions (for debugging and improvement)"""
    normalized_query = normalize_query(query)
    suggestions = []
    
    for task_id, task_data in TASK_DATA.items():
        for task_query in task_data["queries"]:
            normalized_task_query = normalize_query(task_query)
            similarity = SequenceMatcher(None, normalized_query, normalized_task_query).ratio()
            
            if similarity > 0.2:  # Lower threshold for suggestions
                suggestions.append((task_query, similarity))
    
    # Sort by similarity and return top N
    suggestions.sort(key=lambda x: x[1], reverse=True)
    return [suggestion[0] for suggestion in suggestions[:limit]]


# Tool registration schema
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Performs a web search and returns a list of relevant pages. Each result includes a title, URL, and a concise summary (snippet) of the page's content. This tool is ideal for quickly gathering information and identifying the most relevant sources without needing to access the full page content immediately.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords or question"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                },
                "time_range": {
                    "type": "string",
                    "description": "Time range for search results",
                    "enum": ["last_day", "last_week", "last_month", "last_year", "any_time"]
                }
            },
            "required": ["query"]
        }
    }
}


# Register tool function
def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="web_search",
        function=web_search,
        schema=TOOL_SCHEMA,
        description="Search for information on the public internet"
    )


# Auto-register when module is imported
register_tool()