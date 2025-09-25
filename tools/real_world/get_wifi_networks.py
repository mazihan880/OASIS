#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_wifi_networks tool implementation
Scan and list nearby Wi-Fi networks
"""

import json
import random
from typing import Dict, Any, List

def get_wifi_networks(*args, **kwargs) -> Dict[str, Any]:
    """
    Scan and list nearby Wi-Fi networks
    
    Args:
        *args: Positional arguments (not used for this tool)
        **kwargs: Keyword arguments (not used for this tool)
    
    Returns:
        Dict containing the Wi-Fi scan results
    """
    
    try:
        # All Wi-Fi networks from the documentation examples
        all_networks = [
            {
                "ssid": "Morning_Glow_Guest",
                "bssid": "00:1A:2B:3C:4D:5E",
                "signal_strength": -55,
                "gateway_ip": "192.168.1.1"
            },
            {
                "ssid": "LocalBusiness_Secure",
                "bssid": "00:1A:2B:3C:4D:6F",
                "signal_strength": -68,
                "gateway_ip": "192.168.2.1"
            },
            {
                "ssid": "xfinitywifi",
                "bssid": "00:1A:2B:3C:4D:7A",
                "signal_strength": -72,
                "gateway_ip": "10.0.0.1"
            },
            {
                "ssid": "MyHomeNetwork",
                "bssid": "AA:BB:CC:DD:EE:01",
                "signal_strength": -45
            },
            {
                "ssid": "Apartment_3B_WiFi",
                "bssid": "11:22:33:44:55:66",
                "signal_strength": -60
            },
            {
                "ssid": "xfinitywifi",
                "bssid": "FF:EE:DD:CC:BB:AA",
                "signal_strength": -75
            },
            {
                "ssid": "Johnson_Family_5G",
                "bssid": "0A:1B:2C:3D:4E:5F",
                "signal_strength": -60
            },
            {
                "ssid": "xfinitywifi",
                "bssid": "1A:2B:3C:4D:5E:6F",
                "signal_strength": -75
            },
            {
                "ssid": "Smith_Home_WiFi",
                "bssid": "AA:BB:CC:DD:EE:FF",
                "signal_strength": -50
            },
            {
                "ssid": "xfinitywifi",
                "bssid": "11:22:33:44:55:66",
                "signal_strength": -75
            }
        ]
        
        # Remove duplicate networks (same SSID and BSSID)
        unique_networks = []
        seen_combinations = set()
        
        for network in all_networks:
            combination = (network["ssid"], network["bssid"])
            if combination not in seen_combinations:
                unique_networks.append(network)
                seen_combinations.add(combination)
        
        # Randomly select 3-5 networks to simulate realistic scan results
        num_networks = random.randint(3, min(5, len(unique_networks)))
        selected_networks = random.sample(unique_networks, num_networks)
        
        # Sort by signal strength (strongest first)
        selected_networks.sort(key=lambda x: x["signal_strength"], reverse=True)
        
        return {
            "result": {
                "status": "success",
                "networks": selected_networks,
                "tool": "get_wifi_networks",
                "scan_time": f"{random.randint(1, 3)}.{random.randint(1, 9)}s",
                "total_found": len(selected_networks)
            }
        }
        
    except Exception as e:
        return {
            "result": {
                "status": "error",
                "message": f"Failed to scan Wi-Fi networks: {str(e)}",
                "tool": "get_wifi_networks"
            }
        }

# Tool registration schema
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_wifi_networks",
        "description": "Scan and list nearby Wi-Fi networks with network information including SSID, BSSID, and signal strength",
        "parameters": {
            "type": "object",
            "properties": {
                "scan_type": {
                    "type": "string",
                    "description": "Type of scan to perform (optional)",
                    "default": "quick"
                }
            },
            "required": []
        }
    }
}

def register_tool():
    """Register this tool with the tool registry"""
    from ..tool_registry import registry
    registry.register(
        name="get_wifi_networks",
        function=get_wifi_networks,
        schema=TOOL_SCHEMA,
        description="Tool function for get_wifi_networks"
    )

# Auto-register when module is imported
register_tool()
