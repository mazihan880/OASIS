#!/usr/bin/env python3
"""
Trajectory Saver
Trajectory saver - Manage multi-turn conversation trajectory saving
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from difflib import SequenceMatcher


class TrajectorySaver:
    """Trajectory saver"""
    
    def __init__(self, base_dir: str = "./trajectories"):
        """Initialize trajectory saver
        
        Args:
            base_dir: Base save directory
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir = None  # Session directory, created once per test run
    
    def initialize_session(self, model_name: str, test_params: Dict[str, Any] = None) -> str:
        """Initialize test session directory
        
        Args:
            model_name: Model name
            test_params: Test parameters (optional)
            
        Returns:
            Session directory path
        """
        # Create session directory name: model_timestamp_params
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_model_name = model_name.replace("/", "_").replace("\\", "_")
        
        session_name = f"{safe_model_name}_{timestamp}"
        if test_params:
            # Add key parameters to directory name
            if 'mode' in test_params:
                session_name += f"_{test_params['mode']}"
            if 'max_workers' in test_params:
                session_name += f"_w{test_params['max_workers']}"
            if 'temperature' in test_params:
                session_name += f"_t{test_params['temperature']}"
        
        self.session_dir = self.base_dir / session_name
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        return str(self.session_dir)
        
    def save_trajectory(self, 
                       trajectory_data: Dict[str, Any],
                       task_id: str,
                       suggested_tools: List[str] = None,
                       executed_tools: List[str] = None,
                       harm_flags: List[bool] = None,
                       test_case: Dict[str, Any] = None) -> str:
        """Save simplified trajectory data
        
        Args:
            trajectory_data: Complete trajectory data
            task_id: tasksID
            suggested_tools: List of suggested tools
            executed_tools: List of actually executed tools
            harm_flags: Harm flag list
            test_case: Test case data
            
        Returns:
            Saved file path
        """
        try:
            if not self.session_dir:
                raise ValueError("Session directory not initialized. Call initialize_session() first.")
            
            # Clean task ID
            safe_task_id = task_id.replace("/", "_").replace("\\", "_")
            trajectory_file = self.session_dir / f"{safe_task_id}.json"
            
            # Extract message sequence from all iterations
            all_messages = []
            if 'messages' in trajectory_data:
                all_messages = trajectory_data['messages']
            elif 'trajectory' in trajectory_data:
                # Extract messages from trajectory
                for iteration in trajectory_data['trajectory']:
                    if 'messages' in iteration:
                        all_messages.extend(iteration['messages'])
            
            # Calculate tracking statistics
            harm_point_stats = self._calculate_harm_point_stats(
                suggested_tools or [], 
                executed_tools or [], 
                harm_flags or [],
                trajectory_data
            )
            
            # Simplified trajectory data
            simplified_data = {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "messages": all_messages,
                "suggested_tools": suggested_tools or [],
                "executed_tools": executed_tools or [],
                "iterations": trajectory_data.get('iterations', 0),
                "success": trajectory_data.get('success', False),
                "final_answer": trajectory_data.get('final_answer', ''),
                "harm_point_analysis": harm_point_stats,
                "test_case_info": {
                    "harm_flags": harm_flags or [],
                    "total_harm_points": len([f for f in (harm_flags or []) if f]),
                    "total_suggested_tools": len(suggested_tools or [])
                } if test_case else None
            }
            
            with open(trajectory_file, 'w', encoding='utf-8') as f:
                json.dump(simplified_data, f, indent=2, ensure_ascii=False)
            
            return str(trajectory_file)
            
        except Exception as e:
            error_msg = f"Failed to save trajectory for {task_id}: {str(e)}"
            print(f"Warning: {error_msg}")
            return error_msg
    
    def _calculate_harm_point_stats(self, 
                                   suggested_tools: List[str], 
                                   executed_tools: List[str], 
                                   harm_flags: List[bool],
                                   trajectory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate advanced tool execution statistics
        
        Args:
            suggested_tools: List of suggested tools
            executed_tools: List of actually executed tools
            harm_flags: Retain parameter compatibility (deprecated)
            trajectory_data: Trajectory data
            
        Returns:
            Advanced tool execution statistics
        """
        # Basic statistics
        total_suggested = len(suggested_tools)
        unique_executed = len(set(executed_tools))
        total_executed = len(executed_tools)
        
        # Calculate tool execution details
        tool_execution_details = []
        for tool in suggested_tools:
            executed_count = executed_tools.count(tool)
            tool_execution_details.append({
                "tool_name": tool,
                "was_executed": executed_count > 0,
                "execution_count": executed_count,
                "is_repeated": executed_count > 1
            })
        
        # Analyze execution order
        execution_order_analysis = self._analyze_execution_order(suggested_tools, trajectory_data)
        
        # Calculate advanced metrics
        suggested_set = set(suggested_tools)
        executed_set = set(executed_tools)
        
        # Execution rate of suggested tools
        suggested_executed = len(suggested_set.intersection(executed_set))
        suggested_execution_rate = suggested_executed / max(total_suggested, 1)
        
        # Extra tool execution (tools not in suggestions)
        extra_tools = executed_set - suggested_set
        extra_tools_count = len(extra_tools)
        
        # Duplicate execution analysis (based on parameter similarity)
        repeated_tools = []
        logical_filtered_execution = []
        previous_calls = []
        
        # Extract tool call details from trajectory data
        tool_calls_with_params = []
        if 'trajectory' in trajectory_data:
            for iteration in trajectory_data['trajectory']:
                if 'tool_results' in iteration:
                    for tool_result in iteration['tool_results']:
                        tool_name = tool_result.get('tool_name', tool_result.get('name', ''))
                        params = tool_result.get('parameters', {})
                        tool_calls_with_params.append({
                            'tool_name': tool_name,
                            'parameters': params
                        })
        
        # Use parameter similarity to determine duplicate execution
        for i, call in enumerate(tool_calls_with_params):
            tool_name = call['tool_name']
            params = call['parameters']
            
            # Check if duplicate call
            is_duplicate = self._is_duplicate_tool_call(tool_name, params, previous_calls)
            
            if is_duplicate:
                repeated_tools.append(tool_name)
            else:
                logical_filtered_execution.append(tool_name)
                previous_calls.append(call)
        
        repeated_tools_unique = list(set(repeated_tools))
        
        # Use passed harm_flags parameter
        actual_harm_flags = harm_flags
        
        # 4 core analysis dimensions
        four_dimension_analysis = {
            "1_actual_executed_tools": executed_tools,
            "2_logical_filtered_execution": logical_filtered_execution,
            "3_suggested_tools": suggested_tools,
            "4_harm_flags": actual_harm_flags
        }
        
        return {
            "total_tools_suggested": total_suggested,
            "total_tools_executed": total_executed,
            "unique_tools_executed": unique_executed,
            "suggested_tools_executed": suggested_executed,
            "suggested_execution_rate": suggested_execution_rate,
            "overall_execution_rate": total_executed / max(total_suggested, 1),
            "extra_tools_count": extra_tools_count,
            "extra_tools": list(extra_tools),
            "repeated_executions_count": len(repeated_tools),
            "repeated_tools": repeated_tools_unique,
            "tool_execution_details": tool_execution_details,
            "four_dimension_analysis": four_dimension_analysis,
            "execution_order_analysis": execution_order_analysis,
            "duplicate_detection_analysis": {
                "total_calls_analyzed": len(tool_calls_with_params),
                "duplicate_calls_detected": len(repeated_tools),
                "logical_filtered_calls": len(logical_filtered_execution),
                "similarity_threshold_used": 0.9,
                "method": "parameter_similarity_based"
            },
            "summary": f"Executed {suggested_executed}/{total_suggested} suggested tools, Total {total_executed} calls ({len(logical_filtered_execution)} logical non-duplicate calls)"
        }
    
    def _analyze_execution_order(self, suggested_tools: List[str], trajectory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tool execution order
        
        Args:
            suggested_tools: List of suggested tools
            trajectory_data: Trajectory data
            
        Returns:
            Execution order analysis result
        """
        if 'trajectory' not in trajectory_data:
            return {"order_preserved": False, "order_score": 0.0, "execution_sequence": []}
        
        # Extract actual execution sequence
        execution_sequence = []
        for iteration in trajectory_data['trajectory']:
            if 'tool_results' in iteration:
                for tool_result in iteration['tool_results']:
                    tool_name = tool_result.get('tool_name', tool_result.get('name', ''))
                    if tool_name:
                        execution_sequence.append(tool_name)
        
        # Calculate order preservation
        order_score = self._calculate_order_score(suggested_tools, execution_sequence)
        
        # Check if executed in strict order
        suggested_in_execution = [tool for tool in execution_sequence if tool in suggested_tools]
        order_preserved = suggested_in_execution == [tool for tool in suggested_tools if tool in suggested_in_execution]
        
        return {
            "order_preserved": order_preserved,
            "order_score": order_score,
            "execution_sequence": execution_sequence,
            "suggested_in_execution": suggested_in_execution,
            "first_tool_correct": len(execution_sequence) > 0 and len(suggested_tools) > 0 and execution_sequence[0] == suggested_tools[0]
        }
    
    def _calculate_order_score(self, suggested_tools: List[str], execution_sequence: List[str]) -> float:
        """Calculate execution order score
        
        Args:
            suggested_tools: List of suggested tools
            execution_sequence: Actual execution sequence
            
        Returns:
            Order score (0.0-1.0)
        """
        if not suggested_tools or not execution_sequence:
            return 0.0
        
        # Find positions of suggested tools in execution sequence
        positions = {}
        for i, tool in enumerate(execution_sequence):
            if tool in suggested_tools and tool not in positions:
                positions[tool] = i
        
        # Calculate correctness of position order
        correct_pairs = 0
        total_pairs = 0
        
        for i in range(len(suggested_tools)):
            for j in range(i + 1, len(suggested_tools)):
                tool1, tool2 = suggested_tools[i], suggested_tools[j]
                if tool1 in positions and tool2 in positions:
                    total_pairs += 1
                    if positions[tool1] < positions[tool2]:
                        correct_pairs += 1
        
        return correct_pairs / max(total_pairs, 1)
    
    def _calculate_param_similarity(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> float:
        """Calculate similarity between two parameter dictionaries
        
        Args:
            params1: First parameter dictionary
            params2: Second parameter dictionary
            
        Returns:
            Similarity score (0.0-1.0)
        """
        if not params1 and not params2:
            return 1.0
        if not params1 or not params2:
            return 0.0
        
        # Convert parameters to strings for comparison
        str1 = json.dumps(params1, sort_keys=True, ensure_ascii=False)
        str2 = json.dumps(params2, sort_keys=True, ensure_ascii=False)
        
        # Use SequenceMatcher to calculate similarity
        similarity = SequenceMatcher(None, str1, str2).ratio()
        return similarity
    
    def _is_duplicate_tool_call(self, tool_name: str, params: Dict[str, Any], 
                               previous_calls: List[Dict[str, Any]], 
                               similarity_threshold: float = 0.9) -> bool:
        """Determine if duplicate tool call
        
        Args:
            tool_name: Tool name
            params: Current call parameters
            previous_calls: Previous tool call list
            similarity_threshold: Similarity threshold
            
        Returns:
            Whether duplicate call
        """
        for prev_call in previous_calls:
            if prev_call.get('tool_name') == tool_name:
                prev_params = prev_call.get('parameters', {})
                similarity = self._calculate_param_similarity(params, prev_params)
                if similarity >= similarity_threshold:
                    return True
        return False
    
    def load_trajectory(self, file_path: str) -> Dict[str, Any]:
        """Load trajectory data
        
        Args:
            file_path: Trajectory file path
            
        Returns:
            Trajectory data
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_sessions(self, model_name: Optional[str] = None) -> list:
        """List all sessions
        
        Args:
            model_name: Model name filter (optional)
            
        Returns:
            Session directory list
        """
        sessions = []
        for session_dir in self.base_dir.iterdir():
            if session_dir.is_dir():
                if model_name is None or session_dir.name.startswith(f"{model_name}_"):
                    sessions.append(session_dir.name)
        return sorted(sessions)
    
    def list_trajectories(self, session_name: str) -> list:
        """List all trajectory files in session
        
        Args:
            session_name: Session name
            
        Returns:
            Trajectory file list
        """
        session_dir = self.base_dir / session_name
        if not session_dir.exists():
            return []
        
        trajectories = []
        for file_path in session_dir.glob("*.json"):
            trajectories.append(file_path.name)
        return sorted(trajectories)
    
    def create_session_summary(self, session_name: str) -> Dict[str, Any]:
        """Create session summary
        
        Args:
            session_name: Session name
            
        Returns:
            Session summary information
        """
        session_dir = self.base_dir / session_name
        if not session_dir.exists():
            return {}
        
        trajectories = self.list_trajectories(session_name)
        total_tasks = len(trajectories)
        
        # Statistics
        total_iterations = 0
        total_tool_calls = 0
        success_count = 0
        
        for trajectory_file in trajectories:
            try:
                data = self.load_trajectory(session_dir / trajectory_file)
                trajectory = data.get("trajectory", {})
                
                iterations = trajectory.get("iterations", 0)
                total_iterations += iterations
                
                if trajectory.get("success", False):
                    success_count += 1
                
                # Count tool calls
                for step in trajectory.get("trajectory", []):
                    if "tool_results" in step:
                        total_tool_calls += len(step["tool_results"])
                        
            except Exception as e:
                print(f"Processing trajectory file {trajectory_file} error: {e}")
                continue
        
        return {
            "session_name": session_name,
            "total_tasks": total_tasks,
            "success_rate": success_count / total_tasks if total_tasks > 0 else 0,
            "avg_iterations": total_iterations / total_tasks if total_tasks > 0 else 0,
            "total_tool_calls": total_tool_calls,
            "avg_tool_calls": total_tool_calls / total_tasks if total_tasks > 0 else 0
        }