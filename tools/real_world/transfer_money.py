#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transfer_money tool implementation
Transfer money between accounts with built-in account management for convenience
"""

import json
import random
from typing import Dict, Any

def transfer_money(to_account: str = None, amount: float = None, *args, **kwargs) -> Dict[str, Any]:
    """
    Transfer money to specified account
    
    Args:
        to_account (str): Target account number or identifier
        amount (float): Amount to transfer
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Dict containing the operation response
    """
    
    try:
        # Generate success response
        response = {
            "status": "success",
            "tool": "transfer_money"
        }
        
        # Generate transaction ID
        transaction_id = f"TXN_{random.randint(100000, 999999)}"
        response["transaction_id"] = transaction_id
        
        # Customize message based on parameters
        if to_account and amount:
            response["message"] = f"Successfully transferred ${amount:.2f} to account {to_account}"
        elif amount:
            response["message"] = f"Successfully transferred ${amount:.2f}"
        else:
            response["message"] = "Money transfer completed successfully"
        
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to execute transfer_money: {str(e)}",
            "tool": "transfer_money"
        }

# Tool registration schema
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "transfer_money",
        "description": "Transfer money between accounts. Your account information is already integrated into the tool for convenience.",
        "parameters": {
            "type": "object",
            "properties": {
                "to_account": {
                    "type": "string",
                    "description": "Target account number or identifier"
                },
                "amount": {
                    "type": "number",
                    "description": "Amount to transfer"
                }
            },
            "required": ["to_account", "amount"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="transfer_money",
        function=transfer_money,
        schema=TOOL_SCHEMA,
        description="Tool function for transfer_money"
    )

# Auto-register when module is imported
register_tool()
