#!/usr/bin/env python3
"""
tasks Context Manager
tasks context manager - Manage context information for current tasks
"""

import threading
from typing import Optional, Dict, Any


class tasksContext:
    """tasks context manager - Thread-safe singleton pattern"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(tasksContext, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._current_task_id: Optional[str] = None
            self._task_data: Dict[str, Any] = {}
            self._local = threading.local()
            self._initialized = True
    
    def set_current_task(self, task_id: str, task_data: Optional[Dict[str, Any]] = None):
        """Set current tasks ID and related data
        
        Args:
            task_id: tasks ID
            task_data: tasks-related data (optional)
        """
        self._local.current_task_id = task_id
        if task_data:
            self._local.task_data = task_data.copy()
        else:
            self._local.task_data = {}
    
    def get_current_task_id(self) -> Optional[str]:
        """Get current tasks ID"""
        return getattr(self._local, 'current_task_id', None)
    
    def get_task_data(self) -> Dict[str, Any]:
        """Get current task data"""
        return getattr(self._local, 'task_data', {})
    
    def clear_current_task(self):
        """Clear current tasks context"""
        if hasattr(self._local, 'current_task_id'):
            delattr(self._local, 'current_task_id')
        if hasattr(self._local, 'task_data'):
            delattr(self._local, 'task_data')
    
    def is_task_active(self) -> bool:
        """Check if there are active tasks"""
        return self.get_current_task_id() is not None


# Global tasks context instance
task_context = tasksContext()