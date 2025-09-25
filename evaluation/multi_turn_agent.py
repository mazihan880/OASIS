#!/usr/bin/env python3
"""
Multi-turn Function Calling Agent
OpenAI SDK-based multi-turn tool calling Agent implementation
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from openai import OpenAI


class MultiTurnAgent:
    """Multi-turn tool calling Agent"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", max_iterations: int = 50, base_url: str = None, temperature: float = 0.6, timeout: int = 1000, thinking: bool = False):
        """Initialize Agent
        
        Args:
            api_key: OpenAI API key
            model: Model name to use
            max_iterations: Maximum number of iterations
            base_url: Custom API base URL
            temperature: Model temperature parameter
            timeout: Request timeout
        """
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        else:
            self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.timeout = timeout
        self.thinking = thinking

        self.logger = logging.getLogger(__name__)
        

        
    def run(self, 
            user_prompt: str, 
            tools: List[Dict[str, Any]], 
            tool_executor: Callable[[str, Dict[str, Any]], Dict[str, Any]],
            system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Run multi-turn tool calling
        
        Args:
            user_prompt: User input
            tools: Tool definition list (OpenAI format)
            tool_executor: Tool execution function
            system_prompt: System prompt
            
        Returns:
            Result dictionary containing complete trajectory
        """
        # Initialize message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        
        # Trajectory record
        trajectory = []
        iteration = 0
        unique_tools = set()  # Record types of tools used
        
        while iteration < self.max_iterations:
            iteration += 1
            
            try:
                # Record iteration start
                iteration_start = {
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                    "type": "model_call",
                    "messages": messages.copy()
                }
                
                # Call model
                if self.thinking:
                    # Only add extra_body parameter when thinking mode is enabled
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=self.temperature,
                        extra_body={"chat_template_kwargs": {"thinking": True}}
                    )
                else:
                    # Don't add extra_body parameter, maintain compatibility with original API
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=self.temperature
                    )
                
                message = response.choices[0].message
                
                # Handle special response format of qwen3-next-thinking model
                content = message.content
                if content is None and hasattr(message, 'reasoning_content') and message.reasoning_content:
                    content = message.reasoning_content
                elif content is None:
                    # Try to get reasoning_content from original response
                    raw_response = response.model_dump() if hasattr(response, 'model_dump') else response.__dict__
                    if 'choices' in raw_response and len(raw_response['choices']) > 0:
                        choice = raw_response['choices'][0]
                        if 'message' in choice and 'reasoning_content' in choice['message']:
                            content = choice['message']['reasoning_content']
                
                iteration_start["response"] = {
                    "content": content,
                    "tool_calls": [{
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in (message.tool_calls or [])]
                }
                iteration_start["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                
                # Add model response to message list
                messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [{
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in (message.tool_calls or [])]
                })
                
                # Check if there are tool calls
                if message.tool_calls:
                    tool_results = []
                    
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            tool_args = {}
                        
                        self.logger.info(f"Execute tool: {tool_name}, Parameters: {tool_args}")
                        
                        # Record used tools
                        unique_tools.add(tool_name)
                        
                        # Execute tool
                        tool_result = tool_executor(tool_name, tool_args)
                        
                        filtered_result = tool_result
                        
                        # Extract harm flag
                        harm_flag = False
                        if isinstance(filtered_result, dict) and 'harm_flag' in filtered_result:
                            harm_flag = filtered_result['harm_flag']
                            # Remove harm_flag from result returned to model
                            clean_result = {k: v for k, v in filtered_result.items() if k != 'harm_flag'}
                        else:
                            clean_result = filtered_result
                        
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "tool_name": tool_name,
                            "arguments": tool_args,
                            "result": clean_result,  # Result for model (filtered debug and harm_flag)
                            "full_result": tool_result,  # Complete original result saved in trajectory
                            "filtered_result": filtered_result,  # Result after filtering debug
                            "harm_flag": harm_flag,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Add tool result to message list (using cleaned result)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(clean_result, ensure_ascii=False)
                        })
                    
                    iteration_start["tool_results"] = tool_results
                    trajectory.append(iteration_start)
                    
                    # Add delay to avoid concurrency issues
                    time.sleep(2)
                    
                    # Continue to next round
                    continue
                else:
                    # No tool calls, check if contains stop words
                    if content and "###STOP###" in content:
                        iteration_start["stop_reason"] = "stop_token"
                        trajectory.append(iteration_start)
                        break
                    # elif message.content and message.content.strip():
                    #     # Has content but no tool calls, consider as final answer
                    #     iteration_start["stop_reason"] = "final_answer"
                    #     trajectory.append(iteration_start)
                    #     break
                    else:
                        # Continue to next round
                        trajectory.append(iteration_start)
                        
                        # Add delay to avoid concurrency issues
                        time.sleep(2)
                        continue
                        
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if connection error
                is_connection_error = any(keyword in error_str for keyword in [
                    'connection error', 'connection timeout', 'timeout', 
                    'network error', 'connection refused', 'connection reset',
                    'read timeout', 'connect timeout', 'socket timeout'
                ])
                
                # Check if Internal Server Error but may have partial results
                is_internal_server_error = 'internal server error' in error_str or '500' in error_str
                
                error_info = {
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                    "type": "connection_error" if is_connection_error else ("server_error" if is_internal_server_error else "error"),
                    "error": str(e),
                    "is_connection_error": is_connection_error,
                    "is_internal_server_error": is_internal_server_error
                }
                trajectory.append(error_info)
                
                if is_connection_error:
                    self.logger.error(f"Iteration {iteration} Error: Connection error.")
                elif is_internal_server_error:
                    self.logger.warning(f"Iteration {iteration} Encountered Internal Server Error, but continue to next round: {e}")
                    # For Internal Server Error, don't throw exception or end loop, continue to next round
                    # Add delay to avoid concurrency issues
                    time.sleep(1)
                    continue
                else:
                    self.logger.error(f"Iteration {iteration} Error: {e}")
                
                # For connection errors, throw exception for upper retry logic to handle
                # For Internal Server Error, don't throw exception, continue processing
                if is_connection_error and not is_internal_server_error:
                    raise e
        
        # If reached maximum iterations
        if iteration >= self.max_iterations:
            trajectory.append({
                "timestamp": datetime.now().isoformat(),
                "type": "max_iterations_reached",
                "iterations": iteration
            })
        
        # Extract final answer
        final_answer = ""
        if messages and messages[-1]["role"] == "assistant":
            final_answer = messages[-1].get("content", "")
            # Remove stop words
            if "###STOP###" in final_answer:
                final_answer = final_answer.replace("###STOP###", "").strip()
        
        return {
            "final_answer": final_answer,
            "trajectory": trajectory,
            "messages": messages,
            "iterations": iteration,
            "success": len(trajectory) > 0 and trajectory[-1].get("type") != "error",
            "unique_tools": unique_tools
        }
    
    def create_tool_schema(self, tool_name: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create tool schema definition
        
        Args:
            tool_name: Tool name
            description: Tool description
            parameters: Parameter definition
            
        Returns:
            OpenAI format tool definition
        """
        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": parameters
            }
        }