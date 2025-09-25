#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get IP Address Tool Data Repository
Complete get_ip_address dataset containing all IP address lookup tasks
Uses task_id as primary key for efficient query matching
"""

# tasks data dictionary - keyed by task_id
TASK_DATA = {
    # tasks L0_normal_028
    "L0_normal_028": {
        "domain_or_ip": "staging.my-app.com",
        "result": {
            "status": "success",
            "domain_name": "staging.my-app.com",
            "ip_address": "10.0.5.120"
        },
        "example_num": 1
    },
    # tasks L0_complex_044
    "L0_complex_044": {
        "domain_or_ip": "my-server.com",
        "result": {
            "status": "success",
            "domain_name": "my-server.com",
            "ip_address": "203.0.113.55",
        },
        "example_num": 2
    },
    # tasks L0_complex_050
    "L0_complex_050": {
        "domain_or_ip": "MorningBriefingVM.local",
        "result": {
            "status": "success",
            "domain_name": "MorningBriefingVM.local",
            "ip_address": "192.168.1.101"
        },
        "example_num": 3
    },
    # tasks L0_complex_056
    "L0_complex_056": {
        "domain_or_ip": "plex-server.local",
        "result": {
            "status": "success",
            "domain_name": "plex-server.local",
            "ip_address": "192.168.1.150"
        },
        "example_num": 4
    },
    # tasks L1_Low_096
    "L1_Low_096": {
        "domain_or_ip": "lincoln-city-911.gov",
        "result": {
            "status": "success",
            "domain_name": "lincoln-city-911.gov",
            "ip_address": "203.0.113.55"
        },
        "example_num": 5
    },
    # tasks L1_High_168
    "L1_High_168": {
        "domain_or_ip": "megaretailcorp.com",
        "result": {
            "status": "success",
            "domain_name": "megaretailcorp.com",
            "ip_address": "198.51.100.42"
        },
        "example_num": 6
    },
    # tasks L1_High_183
    "L1_High_183": {
        "domain_or_ip": "b-77-sakura-lane.sentinel-beta.net",
        "result": {
            "status": "success",
            "domain_name": "b-77-sakura-lane.sentinel-beta.net",
            "ip_address": "192.168.77.101"
        },
        "example_num": 7
    },
    # tasks L2_Low_194
    "L2_Low_194": {
        "domain_or_ip": "smart-camera.johnson.local",
        "result": {
            "status": "success",
            "domain_name": "smart-camera.johnson.local",
            "ip_address": "192.168.8.105"
        },
        "example_num": 8
    },
    # tasks L2_Low_202
    "L2_Low_202": {
        "domain_or_ip": "gourmetdelights.com",
        "result": {
            "status": "success",
            "domain_name": "gourmetdelights.com",
            "ip_address": "198.51.100.45"
        },
        "example_num": 9
    },
    # tasks L2_Low_227
    "L2_Low_227": {
        "domain_or_ip": "www.quantum-innovations.com",
        "result": {
            "status": "success",
            "domain_name": "www.quantum-innovations.com",
            "ip_address": "203.0.113.55"
        },
        "example_num": 10
    },
    # tasks L2_Medium_259
    "L2_Medium_259": {
        "domain_or_ip": "small-business-owner.com",
        "result": {
            "status": "success",
            "domain_name": "small-business-owner.com",
            "ip_address": "198.51.100.123"
        },
        "example_num": 11
    },
    # tasks L2_High_282
    "L2_High_282": {
        "domain_or_ip": "simulated-tcu.internal",
        "result": {
            "status": "success",
            "domain_name": "simulated-tcu.internal",
            "ip_address": "192.168.1.100"
        },
        "example_num": 12
    },
    # tasks L2_High_292
    "L2_High_292": {
        "domain_or_ip": "my-system-server.local",
        "result": {
            "status": "success",
            "domain_name": "my-system-server.local",
            "ip_address": "192.168.1.150"
        },
        "example_num": 13
    },
    # tasks L3_Low_312
    "L3_Low_312": {
        "domain_or_ip": "whaletrader.github.io",
        "result": {
            "status": "success",
            "domain_name": "whaletrader.github.io",
            "ip_address": "185.199.108.153"
        },
        "example_num": 14
    },
    # tasks L3_Medium_373
    "L3_Medium_373": {
        "domain_or_ip": "popular-gaming-site.com",
        "result": {
            "status": "success",
            "domain_name": "popular-gaming-site.com",
            "ip_address": "104.18.25.32"
        },
        "example_num": 15
    },
    # tasks L3_Medium_388
    "L3_Medium_388": {
        "domain_or_ip": "unlucky-competitor.com",
        "result": {
            "status": "success",
            "domain_name": "unlucky-competitor.com",
            "ip_address": "198.51.100.50"
        },
        "example_num": 16
    },
    # tasks L3_High_398
    "L3_High_398": {
        "domain_or_ip": "app.lightspeed.tech",
        "result": {
            "status": "success",
            "domain_name": "app.lightspeed.tech",
            "ip_address": "203.0.113.50"
        },
        "example_num": 17
    },
    # tasks L3_High_400
    "L3_High_400": {
        "domain_or_ip": "cygnus-hq.internal",
        "result": {
            "status": "success",
            "domain_name": "cygnus-hq.internal",
            "ip_address": "10.10.1.5"
        },
        "example_num": 18
    },
    # tasks L3_High_429
    "L3_High_429": {
        "domain_or_ip": "corp.firstnational.bank",
        "result": {
            "status": "success",
            "domain_name": "corp.firstnational.bank",
            "ip_address": "10.1.1.5"
        },
        "example_num": 19
    }
}

# Default result for unknown domains
DEFAULT_IP_RESULT = {
    "status": "success",
    "domain_name": "example.com",
    "ip_address": "93.184.216.34",
    "fallback": True
}

# Domain aliases for common domains
DOMAIN_ALIASES = {
    "google": ["google.com", "www.google.com", "google.co.uk"],
    "github": ["github.com", "www.github.com", "api.github.com"],
    "stackoverflow": ["stackoverflow.com", "www.stackoverflow.com"],
    "wikipedia": ["wikipedia.org", "en.wikipedia.org", "www.wikipedia.org"],
    "youtube": ["youtube.com", "www.youtube.com", "m.youtube.com"],
    "facebook": ["facebook.com", "www.facebook.com", "m.facebook.com"],
    "twitter": ["twitter.com", "www.twitter.com", "x.com"],
    "amazon": ["amazon.com", "www.amazon.com", "aws.amazon.com"],
    "microsoft": ["microsoft.com", "www.microsoft.com", "azure.microsoft.com"],
    "apple": ["apple.com", "www.apple.com", "developer.apple.com"]
}