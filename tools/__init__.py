#!/usr/bin/env python3
"""
Tools Module
Tool module - Provide tool support for Agent security testing
"""

from .tool_registry import registry

# Import tool packages to trigger auto-registration
from . import real_world
from . import resource

__all__ = ['registry', 'real_world', 'resource']