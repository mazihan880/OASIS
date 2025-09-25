#!/usr/bin/env python3
"""
Direct Evaluation Tools Module
Direct evaluation tool module - For direct eval mode testing
"""

# For simplicity, direct_eval mode uses same tools as real_world
# But can have different implementation or configuration
from ..real_world import (
    get_all_tools, execute_tool
)

__all__ = [
    'get_all_tools',
    'execute_tool'
]