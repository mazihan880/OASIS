#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze Sentiment Tool - tasks-Aware Version
Performs sentiment analysis on text content from various sources including social media, reviews, and comments
"""

import sys
import os
import re
import json
from typing import Dict, Any, List, Optional

# Add the tools directory to the path for imports
tools_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, tools_dir)

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

# Import resource data with fallback
try:
    from tools.resource.analyze_sentiment_data import TASKS, DEFAULT_RESPONSE
except ImportError:
    try:
        # Try relative import
        from ..resource.analyze_sentiment_data import TASKS, DEFAULT_RESPONSE
    except ImportError:
        # Fallback data if import fails
        TASKS = {}
    DEFAULT_RESPONSE = {
        "status": "success",
        "sentiment": "neutral",
        "score": 0.0,
        "summary": "Analysis completed",
        "details": {
            "confidence": 0.8,
            "keywords": [],
            "emotions": {
                "joy": 0.0,
                "anger": 0.0,
                "fear": 0.0,
                "sadness": 0.0,
                "surprise": 0.0,
                "disgust": 0.0
            }
        }
    }

def extract_keywords_from_text(text: str) -> List[str]:
    """
    Extract potential keywords from text for sentiment analysis
    """
    if not text:
        return []
    
    # Common sentiment-related keywords
    positive_keywords = [
        'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like',
        'good', 'best', 'awesome', 'perfect', 'brilliant', 'outstanding', 'excited',
        'happy', 'pleased', 'satisfied', 'impressed', 'recommend', 'positive'
    ]
    
    negative_keywords = [
        'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'worst',
        'poor', 'disappointing', 'frustrated', 'angry', 'upset', 'sad',
        'negative', 'problem', 'issue', 'complaint', 'wrong', 'broken'
    ]
    
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in positive_keywords + negative_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords

def calculate_basic_sentiment(text: str) -> Dict[str, Any]:
    """
    Calculate basic sentiment score based on text content
    """
    if not text:
        return {"sentiment": "neutral", "score": 0.0, "confidence": 0.5}
    
    text_lower = text.lower()
    
    # Simple keyword-based sentiment analysis
    positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'like', 'best', 'awesome', 'happy', 'excited']
    negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'angry', 'sad', 'disappointed']
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total_words = len(text.split())
    
    if positive_count > negative_count:
        sentiment = "positive"
        score = min(0.9, (positive_count - negative_count) / max(total_words, 1) * 10)
    elif negative_count > positive_count:
        sentiment = "negative"
        score = max(-0.9, -(negative_count - positive_count) / max(total_words, 1) * 10)
    else:
        sentiment = "neutral"
        score = 0.0
    
    confidence = min(0.9, abs(score) + 0.3)
    
    return {
        "sentiment": sentiment,
        "score": score,
        "confidence": confidence
    }

def calculate_call_similarity(text: str, source: str, call_data: Dict[str, Any]) -> float:
    """
    Calculate similarity score between input and a specific call
    """
    score = 0.0
    text_lower = text.lower()
    
    # Check query parameters
    if 'text' in call_data and call_data['text']:
        call_text = call_data['text'].lower()
        # Simple keyword matching
        common_words = set(text_lower.split()) & set(call_text.split())
        score += len(common_words) * 10
    
    if 'source' in call_data and source:
        if call_data['source'] == source:
            score += 15
    
    return score

def find_matching_task(text: str, source: str = None, call_index: int = None) -> tuple:
    """
    Find the best matching task for the given text and source
    Returns (task_id, task_data, call_index) for calls structure or (task_id, task_data, None) for legacy
    """
    if not text:
        return None, None, None
    
    text_lower = text.lower()
    best_match = None
    best_score = 0
    best_task_id = None
    best_call_index = None
    
    # Look for keyword matches in the text
    for task_id, task_data in TASKS.items():
        # Check if task has calls structure
        if 'calls' in task_data and isinstance(task_data['calls'], list) and len(task_data['calls']) > 0:
            # Handle calls structure
            for call_idx, call_data in enumerate(task_data['calls']):
                if call_index is not None and call_idx != call_index:
                    continue
                    
                score = calculate_call_similarity(text, source or "text", call_data)
                
                if score > best_score:
                    best_score = score
                    best_match = task_data
                    best_task_id = task_id
                    best_call_index = call_idx
        else:
            # Handle legacy structure
            score = 0
            result = task_data.get('result', {})
            query = task_data.get('query', {})
            
            # Check for query text keyword matches (higher priority)
            if 'text' in query:
                query_keywords = query['text']
                for keyword in query_keywords:
                    if keyword.lower() in text_lower:
                        score += 15  # Higher score for query matches
            
            # Check for result keyword matches
            if 'keywords' in result:
                keywords = result['keywords']
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        score += 10
            
            # Check for source matches
            if source and 'source' in query:
                query_sources = query['source']
                if source in query_sources:
                    score += 8
            
            # Check for sentiment matches
            if 'sentiment' in result:
                basic_sentiment = calculate_basic_sentiment(text)
                if basic_sentiment['sentiment'] == result['sentiment']:
                    score += 5
            
            # Check for specific content patterns (legacy support)
            if 'product' in text_lower and 'L0_complex_041' in task_id:
                score += 20
            elif 'poll' in text_lower and 'L3_Low_337' in task_id:
                score += 20
            elif 'comment' in text_lower and any(x in task_id for x in ['L3_Low', 'L3_Medium']):
                score += 15
            elif 'tweet' in text_lower or 'social' in text_lower:
                score += 10
            
            if score > best_score:
                best_score = score
                best_match = task_data
                best_task_id = task_id
                best_call_index = None
    
    if best_score > 10:
        return best_task_id, best_match, best_call_index
    return None, None, None

def analyze_sentiment(text, source="text", analysis_depth="detailed", include_keywords=True, include_emotions=True):
    """
    Analyze sentiment of text content with task context support
    
    Args:
        text: Text content to analyze
        source: Source type of the text
        analysis_depth: Level of analysis detail
        include_keywords: Whether to include keyword extraction
        include_emotions: Whether to include emotion analysis
    
    Returns:
        dict: Sentiment analysis result or error message
    """
    # Handle None or non-string inputs
    if text is None:
        return {
            "result": {
                "status": "error",
                "message": "Text cannot be None"
            },
                "method": "parameter_validation",
                "task_active": False,
                "matched_task": False,
                "multi_call": False,
                "matched_task_id": None
            }
        }
    
    # Convert non-string inputs to string
    if not isinstance(text, str):
        text = str(text)
    
    # Handle empty or whitespace-only text
    if not text.strip():
        return {
            "result": {
                "status": "error",
                "message": "Text cannot be empty"
            },
                "method": "parameter_validation",
                "task_active": False,
                "matched_task": False,
                "multi_call": False,
                "matched_task_id": None
            }
        }
    
    # Validate source parameter
    valid_sources = ["review", "comment", "tweet", "post", "feedback", "forum", "chat", "email", "text"]
    if source not in valid_sources:
        source = "text"  # Default fallback
    
    # Validate analysis_depth parameter
    valid_depths = ["basic", "detailed", "comprehensive"]
    if analysis_depth not in valid_depths:
        analysis_depth = "detailed"  # Default fallback
    
    # Priority 1: Use task context data if available
    if task_context.is_task_active():
        current_task_id = task_context.get_current_task_id()
        if current_task_id and current_task_id in TASKS:
            task_data = TASKS[current_task_id]
            # Handle calls structure - directly return the predefined result without query matching
            if 'calls' in task_data and isinstance(task_data['calls'], list) and len(task_data['calls']) > 0:
                # Always use the first call's result (or you can modify this to use a specific call)
                result = task_data['calls'][0].get('result', {}).copy()
                
                    "method": "task_context_direct",
                    "matched_task_id": current_task_id,
                    "task_active": True,
                    "matched_task": True,
                    "multi_call": True,
                    "note": "Direct return without query matching"
                }
                return {
                    "result": result,
                }
            else:
                # Handle legacy structure - directly return the predefined result
                result = task_data["result"].copy()
                    "method": "task_context_direct",
                    "matched_task_id": current_task_id,
                    "task_active": True,
                    "matched_task": True,
                    "multi_call": False,
                    "note": "Direct return without query matching"
                }
                return {
                    "result": result,
                }
    
    # Validate boolean parameters
    if not isinstance(include_keywords, bool):
        include_keywords = True  # Default fallback
    
    if not isinstance(include_emotions, bool):
        include_emotions = True  # Default fallback
    
    # Priority 2: Fallback to intelligent matching
    task_id, best_task, call_index = find_matching_task(text, source)
    
    if best_task:
        # Handle calls structure
        if call_index is not None and 'calls' in best_task:
            call_data = best_task['calls'][call_index]
            result = call_data.get('result', {}).copy()
        else:
            # Handle legacy structure
            result = best_task["result"].copy()
        
        # Filter result based on parameters
        if not include_keywords and "keywords" in result:
            result["keywords"] = []
        
        if not include_emotions and "emotions" in result:
            result["emotions"] = {}
        
        # Adjust result based on analysis_depth
        if analysis_depth == "basic":
            # Keep only basic sentiment info
            basic_result = {
                "status": result.get("status", "success"),
                "sentiment": result.get("sentiment", "neutral"),
                "score": result.get("score", 0.0)
            }
            return basic_result
        
        # Add debug metadata
            'method': 'intelligent_matching',
            'matched_task_id': task_id,
            'call_index': call_index,
            'matched_task': True,
            'multi_call': call_index is not None,
            'task_active': task_context.is_task_active()
        }
        return {
            'result': result,
        }
    else:
        # Generate fallback result
        result = {
            "status": "success",
            "sentiment": "neutral",
            "score": 0.0,
            "summary": "Sentiment analysis completed for text content",
            "confidence": 0.3,
            "keywords": [] if include_keywords else [],
            "emotions": {} if include_emotions else {}
        }
            "method": "fallback",
            "matched_task": False,
            "multi_call": False,
            "matched_task_id": None,
            "task_active": task_context.is_task_active()
        }
        return {
            "result": result,
        }

# Tool schema for integration
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "analyze_sentiment",
        "description": "Analyze sentiment of text content from various sources including social media posts, reviews, comments, and other text data. Supports different analysis modes and output formats for various use cases.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text content to analyze for sentiment. Can be social media posts, product reviews, customer feedback, comments, or any text requiring sentiment analysis."
                },
                "source": {
                    "type": "string",
                    "description": "The source type of the text for context-aware analysis",
                    "enum": ["review", "comment", "tweet", "post", "feedback", "forum", "chat", "email", "text"],
                    "default": "text"
                },
                "analysis_depth": {
                    "type": "string",
                    "description": "Level of analysis detail required",
                    "enum": ["basic", "detailed", "comprehensive"],
                    "default": "detailed"
                },
                "include_keywords": {
                    "type": "boolean",
                    "description": "Whether to include keyword extraction in the analysis",
                    "default": True
                },
                "include_emotions": {
                    "type": "boolean",
                    "description": "Whether to include detailed emotion analysis",
                    "default": True
                }
            },
            "required": ["text"]
        }
    }
}

def main():
    """Test the tool with sample texts"""
    test_cases = [
        {
            "text": "This is a great product! I love it and would definitely recommend it to others.",
            "source": "review"
        },
        {
            "text": "This poll is clearly biased! The questions are leading and don't represent real voter concerns.",
            "source": "comment"
        },
        {
            "text": "I'm feeling really anxious about work deadlines and having imposter syndrome.",
            "source": "post"
        },
        {
            "text": "The new product launch was amazing! So excited about the innovative features.",
            "source": "tweet"
        },
        {
            "text": "This is terrible service. I hate this company and will never use them again.",
            "source": "review"
        },
        {
            "text": "The weather is nice today.",
            "source": "comment"
        }
    ]
    
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Text: {test_case['text']}")
        print(f"Source: {test_case['source']}")
        result = analyze_sentiment(test_case['text'], test_case['source'])
        print(f"Result: {json.dumps(result, indent=2)}")
        print("-" * 30)

if __name__ == "__main__":
    main()

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="analyze_sentiment",
        function=analyze_sentiment,
        schema=TOOL_SCHEMA,
        description="Tool function: analyze_sentiment"
    )


# Auto-register when module is imported
register_tool()
