#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_to_shopping_cart tool implementation
Add items to online shopping cart
"""

import json
import random
from typing import Dict, Any

def add_to_shopping_cart(*args, **kwargs) -> Dict[str, Any]:
    """
    Add items to online shopping cart
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Dict containing the operation response
    """
    
    try:
        # Generate success response
        return {
            "result": {
                "status": "success",
                "message": "Item successfully added to shopping cart",
                "tool": "add_to_shopping_cart",
                "cart_item_count": random.randint(1, 10)
            }
        }
        
    except Exception as e:
        return {
            "result": {
                "status": "error",
                "message": f"Failed to execute add_to_shopping_cart: {str(e)}",
                "tool": "add_to_shopping_cart"
            }
        }

# Tool registration schema
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "add_to_shopping_cart",
        "description": "Add items to online shopping cart",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product ID to add to cart(Optional, if not provided, it will use the first product's id in the product list)"
                },
                "quantity": {
                    "type": "integer",
                    "description": "Quantity of the product to add",
                    "minimum": 1
                },
                "cart_id": {
                    "type": "string",
                    "description": "Shopping cart ID (optional, creates new cart if not provided)"
                },
                "size": {
                    "type": "string",
                    "description": "Product size (if applicable)"
                },
                "color": {
                    "type": "string",
                    "description": "Product color (if applicable)"
                }
            },
            "required": ["product_id", "quantity"]
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="add_to_shopping_cart",
        function=add_to_shopping_cart,
        schema=TOOL_SCHEMA,
        description="Tool function for add_to_shopping_cart"
    )

# Auto-register when module is imported
register_tool()
