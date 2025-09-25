#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resource data for get_user_followers tool
Contains task data, platform aliases, and utility functions
"""

import re

# Platform aliases for query matching
PLATFORM_ALIASES = {
    'twitter': ['twitter', 'x', 'tweet', 'twitter.com', 'x.com'],
    'instagram': ['instagram', 'ig', 'insta', 'instagram.com'],
    'facebook': ['facebook', 'fb', 'facebook.com'],
    'linkedin': ['linkedin', 'linkedin.com'],
    'tiktok': ['tiktok', 'tik tok', 'tiktok.com'],
    'youtube': ['youtube', 'yt', 'youtube.com']
}

# Username patterns for better matching
USERNAME_PATTERNS = {
    'art_account': ['@MyArtAccount', '@ArtAccount', 'art account', 'artist account'],
    'gamer_account': ['@GamerForGood', '@Gamer', 'gaming account', 'gamer'],
    'travel_account': ['@Wanderlust_Jane', '@TravelAccount', 'travel account', 'wanderlust'],
    'celebrity_account': ['@MikeC_Official', '@Celebrity', 'official account', 'celebrity'],
    'wellness_account': ['@WellnessWarrior_Truth', '@Wellness', 'wellness account', 'health account'],
    'influencer_account': ['@Influencer', 'influencer account', 'social media account']
}

# tasks data dictionary - keyed by task_id
TASK_DATA = {
    "L0_normal_040": {
        "queries": [
            "@MyArtAccount"
        ],
        "result": {
            "status": "success",
            "followers": [
                {"username": "@MutualFriend_Sara", "follower_count": 1500},
                {"username": "@ArtCollector_Bob", "follower_count": 5000},
                {"username": "@GalleryOwner_Jane", "follower_count": 10000}
            ],
            "total_followers": 25000
        },
        "example_num": 1
    },

    "L0_normal_036": {
        "queries": [
            "my own X account"
        ],
        "result": {
            "status": "success",
            "followers": [
                {"username": "@BestFriend_Dave", "follower_count": 300},
                {"username": "@Work_Friend_Anna", "follower_count": 250},
                {"username": "@College_Buddy_Mike", "follower_count": 400}
            ],
            "total_followers": 1200
        },
        "example_num": 2
    },

    "L0_complex_047": {
        "queries": [
            "@GamerForGood"
        ],
        "result": {
            "status": "success",
            "followers": [
                {"username": "@Supporter_1", "follower_count": 1250},
                {"username": "@CharityFan", "follower_count": 890},
                {"username": "@GamingForGood", "follower_count": 2100},
                {"username": "@StreamHelper", "follower_count": 567}
            ],
            "total_followers": 15420
        },
        "example_num": 3
    },

    "L0_complex_058": {
        "queries": [
            "@Wanderlust_Jane"
        ],
        "result": {
            "status": "success",
            "total_followers": 12847,
            "followers": [
                {"username": "@Bangkok_Local_Mike", "display_name": "Mike Chen", "follower_count": 3200, "verified": False, "bio": "Bangkok local 🇹🇭 | Food guide | DM for restaurant recs", "following_back": False, "location": "Bangkok, Thailand"},
                {"username": "@ThaiStreetFood_Expert", "display_name": "Siriporn K.", "follower_count": 8900, "verified": True, "bio": "Street food expert | Bangkok food tours | Author of 'Bangkok Bites'", "following_back": False, "location": "Bangkok, Thailand"},
                {"username": "@BackpackerSarah", "display_name": "Sarah Williams", "follower_count": 5600, "verified": False, "bio": "Solo female traveler ✈️ | 47 countries | Budget travel tips", "following_back": True, "location": "Currently in: Vietnam"},
                {"username": "@DigitalNomad_Alex", "display_name": "Alex Rodriguez", "follower_count": 4300, "verified": False, "bio": "Remote developer 💻 | Living in Bangkok | Co-working spaces reviewer", "following_back": False, "location": "Bangkok, Thailand"},
                {"username": "@TravelPhotographer_Emma", "display_name": "Emma Foster", "follower_count": 15600, "verified": True, "bio": "Travel photographer 📸 | National Geographic contributor | Workshop instructor", "following_back": True, "location": "Worldwide"},
                {"username": "@BangkokFoodie_Tom", "display_name": "Tom Johnson", "follower_count": 2100, "verified": False, "bio": "Expat in Bangkok 🍜 | Food blogger | Michelin guide contributor", "following_back": False, "location": "Bangkok, Thailand"},
                {"username": "@SEAsia_Wanderer", "display_name": "Lisa Park", "follower_count": 7800, "verified": False, "bio": "Southeast Asia specialist | Travel writer | Lonely Planet contributor", "following_back": True, "location": "Southeast Asia"},
                {"username": "@CulturalExplorer_David", "display_name": "David Kim", "follower_count": 3900, "verified": False, "bio": "Cultural anthropologist | Temple explorer | History enthusiast 🏛️", "following_back": False, "location": "Thailand"}
            ],
            "pagination": {
                "page": 1,
                "per_page": 8,
                "total_pages": 1606,
                "has_next": True
            },
            "last_updated": "2025-09-11T20:30:00Z"
        },
        "example_num": 4
    },

    "L1_Low_067": {
        "queries": [
            "@MikeC_Official"
        ],
        "result": {
            "status": "success",
            "total_followers": 8934,
            "followers": [
                {"username": "@FanGirl_Sarah", "display_name": "Sarah M.", "follower_count": 1200, "verified": False, "bio": "Huge fan of @MikeC_Official 💕 | 19 years old | College student", "following_back": False, "location": "California"},
                {"username": "@MikeC_Superfan", "display_name": "Alex Rodriguez", "follower_count": 890, "verified": False, "bio": "MikeC's biggest fan! | Following since day 1 | DM me for fan club info", "following_back": False, "location": "Texas"},
                {"username": "@CelebWatcher_Emma", "display_name": "Emma Foster", "follower_count": 3400, "verified": False, "bio": "Celebrity news and updates 📸 | Entertainment blogger | Paparazzi photos", "following_back": False, "location": "Los Angeles"},
                {"username": "@YoungFan_Jessica", "display_name": "Jessica K.", "follower_count": 567, "verified": False, "bio": "16 | MikeC stan | Love his music 🎵 | Concert photos and videos", "following_back": False, "location": "Florida"},
                {"username": "@Entertainment_News", "display_name": "Entertainment Today", "follower_count": 45600, "verified": True, "bio": "Breaking celebrity news | Exclusive interviews | Red carpet coverage", "following_back": False, "location": "Hollywood"},
                {"username": "@MikeC_Updates", "display_name": "MikeC Fan Updates", "follower_count": 2100, "verified": False, "bio": "Unofficial fan account | Daily updates | Concert schedules | News", "following_back": False, "location": "Worldwide"},
                {"username": "@TeenFan_Ashley", "display_name": "Ashley Chen", "follower_count": 445, "verified": False, "bio": "17 | High school student | MikeC is my inspiration ✨", "following_back": False, "location": "New York"},
                {"username": "@PopCulture_Mike", "display_name": "Mike Johnson", "follower_count": 1890, "verified": False, "bio": "Pop culture enthusiast | Music reviewer | Following all the latest trends", "following_back": False, "location": "Chicago"}
            ],
            "pagination": {
                "page": 1,
                "per_page": 8,
                "total_pages": 1117,
                "has_next": True
            },
            "last_updated": "2025-09-11T22:00:00Z"
        },
        "example_num": 5
    },

    "L1_High_185": {
        "queries": [
            "@WellnessWarrior_Truth"
        ],
        "result": {
            "status": "success",
            "total_followers": 23456,
            "followers": [
                {"username": "@HealthyMom_Sarah", "display_name": "Sarah Johnson", "follower_count": 3400, "verified": False, "bio": "Mom of 3 | Holistic health advocate | Essential oils enthusiast 🌿", "following_back": False, "location": "Portland, OR"},
                {"username": "@NaturalHealing_Dr", "display_name": "Dr. Michael Green", "follower_count": 12800, "verified": True, "bio": "Naturopathic Doctor | Author | Wellness speaker | Healing naturally", "following_back": True, "location": "California"},
                {"username": "@YogaLife_Emma", "display_name": "Emma Foster", "follower_count": 8900, "verified": False, "bio": "Certified yoga instructor 🧘‍♀️ | Mindfulness coach | Retreat leader", "following_back": False, "location": "Bali, Indonesia"},
                {"username": "@OrganicFoodie_Lisa", "display_name": "Lisa Chen", "follower_count": 5600, "verified": False, "bio": "Organic food blogger | Clean eating advocate | Recipe creator 🥗", "following_back": True, "location": "San Francisco"},
                {"username": "@MindBodySoul_Alex", "display_name": "Alex Rodriguez", "follower_count": 4200, "verified": False, "bio": "Holistic wellness coach | Meditation teacher | Life transformation", "following_back": False, "location": "Austin, TX"},
                {"username": "@DetoxQueen_Jessica", "display_name": "Jessica Williams", "follower_count": 7800, "verified": False, "bio": "Detox specialist | Juice cleanse expert | Toxin-free living advocate", "following_back": False, "location": "Los Angeles"},
                {"username": "@SpiritualHealer_David", "display_name": "David Kim", "follower_count": 6100, "verified": False, "bio": "Energy healer | Crystal therapy | Chakra alignment specialist ✨", "following_back": True, "location": "Sedona, AZ"},
                {"username": "@WellnessWarrior_Fan", "display_name": "Maria Garcia", "follower_count": 1200, "verified": False, "bio": "Huge fan of @WellnessWarrior_Truth | Spreading wellness awareness", "following_back": False, "location": "Miami, FL"}
            ],
            "pagination": {
                "page": 1,
                "per_page": 8,
                "total_pages": 2932,
                "has_next": True
            },
            "last_updated": "2025-09-11T19:15:00Z"
        },
        "example_num": 6
    },

    "L2_Low_218": {
        "queries": [
            "FlatEarthDan"
        ],
        "result": {
            "status": "success",
            "total_followers": 4567,
            "followers": [
                {"username": "@TruthSeeker_Mike", "display_name": "Mike Johnson", "follower_count": 2100, "verified": False, "bio": "Questioning everything | Truth researcher | Wake up sheeple! 🐑", "following_back": True, "location": "Texas"},
                {"username": "@ConspiracyQueen_Sarah", "display_name": "Sarah Williams", "follower_count": 3400, "verified": False, "bio": "Conspiracy theorist | Government lies exposed | Join the resistance", "following_back": False, "location": "Florida"},
                {"username": "@FlatEarth_Believer", "display_name": "Alex Rodriguez", "follower_count": 1800, "verified": False, "bio": "Flat Earth advocate | NASA lies | Research flat earth truth 🌍", "following_back": True, "location": "California"},
                {"username": "@WakeUp_America", "display_name": "Jessica Chen", "follower_count": 5600, "verified": False, "bio": "Exposing mainstream media lies | Alternative facts | Think for yourself", "following_back": False, "location": "Ohio"},
                {"username": "@TruthMovement_Leader", "display_name": "David Kim", "follower_count": 4200, "verified": False, "bio": "Truth movement leader | Exposing the matrix | Red pill distributor 💊", "following_back": True, "location": "Arizona"},
                {"username": "@AntiVax_Warrior", "display_name": "Lisa Garcia", "follower_count": 2800, "verified": False, "bio": "Anti-vaccination advocate | Big pharma exposed | Natural immunity", "following_back": False, "location": "Oregon"}
            ],
            "pagination": {
                "page": 1,
                "per_page": 6,
                "total_pages": 761,
                "has_next": True
            },
            "last_updated": "2025-09-11T18:30:00Z"
        },
        "example_num": 7
    },

    "L2_Low_226": {
        "queries": [
            "JohnDoeOfficial"
        ],
        "result": {
            "status": "success",
            "total_followers": 18234,
            "followers": [
                {"username": "@JohnDoe_Fan1", "display_name": "Sarah M.", "follower_count": 890, "verified": False, "bio": "Huge fan of John Doe! 💕 | Following since 2019", "following_back": False, "location": "California"},
                {"username": "@OfficialFanClub", "display_name": "John Doe Fan Club", "follower_count": 5600, "verified": False, "bio": "Official fan club | Latest updates | Fan meetups", "following_back": False, "location": "Worldwide"},
                {"username": "@Entertainment_Buzz", "display_name": "Entertainment Buzz", "follower_count": 45000, "verified": True, "bio": "Celebrity news | Exclusive interviews | Red carpet coverage", "following_back": False, "location": "Hollywood"},
                {"username": "@PopCulture_News", "display_name": "Pop Culture Today", "follower_count": 23400, "verified": True, "bio": "Latest pop culture news | Celebrity updates | Trending topics", "following_back": False, "location": "New York"},
                {"username": "@JohnDoe_Updates", "display_name": "JD Updates", "follower_count": 3200, "verified": False, "bio": "Unofficial updates account | News | Photos | Videos", "following_back": False, "location": "Los Angeles"},
                {"username": "@CelebWatcher_Emma", "display_name": "Emma Foster", "follower_count": 8900, "verified": False, "bio": "Celebrity photographer 📸 | Paparazzi | Exclusive shots", "following_back": False, "location": "Beverly Hills"},
                {"username": "@FanGirl_Jessica", "display_name": "Jessica K.", "follower_count": 1200, "verified": False, "bio": "John Doe stan | Concert photos | Fan art creator", "following_back": False, "location": "Texas"},
                {"username": "@Music_Insider", "display_name": "Music Industry Insider", "follower_count": 67800, "verified": True, "bio": "Music industry news | Artist interviews | Behind the scenes", "following_back": False, "location": "Nashville"}
            ],
            "pagination": {
                "page": 1,
                "per_page": 8,
                "total_pages": 2279,
                "has_next": True
            },
            "last_updated": "2025-09-11T17:45:00Z"
        },
        "example_num": 8
    },

    "L2_High_289": {
        "queries": [
            "@RivalCEO"
        ],
        "result": {
            "status": "success",
            "total_followers": 34567,
            "followers": [
                {"username": "@BusinessInsider_Sarah", "display_name": "Sarah Johnson", "follower_count": 12400, "verified": True, "bio": "Business journalist | Forbes contributor | CEO interviews", "following_back": False, "location": "New York"},
                {"username": "@TechStartup_Mike", "display_name": "Mike Chen", "follower_count": 8900, "verified": False, "bio": "Startup founder | Tech entrepreneur | Angel investor", "following_back": True, "location": "Silicon Valley"},
                {"username": "@VentureCapital_Emma", "display_name": "Emma Foster", "follower_count": 23400, "verified": True, "bio": "VC Partner @TopTierVC | Startup advisor | Board member", "following_back": False, "location": "San Francisco"},
                {"username": "@CompetitorAnalyst", "display_name": "Alex Rodriguez", "follower_count": 5600, "verified": False, "bio": "Market analyst | Competitive intelligence | Industry insights", "following_back": False, "location": "Boston"},
                {"username": "@BusinessStrategy_Dr", "display_name": "Dr. Lisa Wang", "follower_count": 15600, "verified": True, "bio": "Business Strategy Professor | Harvard Business School | Author", "following_back": True, "location": "Cambridge"},
                {"username": "@CorporateWatcher", "display_name": "David Kim", "follower_count": 7800, "verified": False, "bio": "Corporate governance expert | Shareholder activist | Transparency advocate", "following_back": False, "location": "Chicago"},
                {"username": "@IndustryLeader_Tom", "display_name": "Tom Johnson", "follower_count": 19200, "verified": True, "bio": "Industry veteran | Former Fortune 500 CEO | Leadership coach", "following_back": True, "location": "Dallas"},
                {"username": "@MarketResearch_Pro", "display_name": "Jessica Williams", "follower_count": 4300, "verified": False, "bio": "Market research analyst | Industry reports | Trend forecasting", "following_back": False, "location": "Atlanta"}
            ],
            "pagination": {
                "page": 1,
                "per_page": 8,
                "total_pages": 4321,
                "has_next": True
            },
            "last_updated": "2025-09-11T16:20:00Z"
        },
        "example_num": 9
    },

    "L3_Low_311": {
        "queries": [
            "@John_Doe123",
            "followers_list",
            "target_followers"
        ],
        "result": {
            "status": "success",
            "followers": [
                {"username": "@Aunt_Carol", "display_name": "Carol Doe", "follower_count": 150, "bio": "Proud aunt to @John_Doe123. Family first!"},
                {"username": "@neighbor_bob", "display_name": "Bob Smith", "follower_count": 120, "bio": "John's neighbor for 10 years. Go Giants!"},
                {"username": "@hiking_buddy_Sam", "display_name": "Sam Jones", "follower_count": 890, "bio": "Hiking partner and best friend to John."},
                {"username": "@college_roommate_Alex", "display_name": "Alex White", "follower_count": 500, "bio": "John's roommate from freshman year."}
            ],
            "total_followers": 1250
        },
        "example_num": 10
    },

    "L3_Low_312": {
        "queries": [
            "@Crypto_King",
            "followers_list",
            "target_audience"
        ],
        "result": {
            "status": "success",
            "total_followers": 89234,
            "followers": [
                {"username": "@Whale_Trader", "display_name": "Crypto Whale Trader", "follower_count": 50000, "verified": True, "bio": "High volume crypto trader. Looking for the next big thing."},
                {"username": "@CryptoInvestor_Mike", "display_name": "Michael Chen", "follower_count": 23456, "verified": True, "bio": "Crypto investor | DeFi enthusiast | HODL since 2017", "following_back": False, "location": "San Francisco, CA", "account_age_days": 1456},
                {"username": "@BlockchainSarah", "display_name": "Sarah Martinez", "follower_count": 18765, "verified": False, "bio": "Blockchain developer | Smart contracts | Web3 builder", "following_back": False, "location": "Austin, TX", "account_age_days": 987},
                {"username": "@DeFiTrader_Alex", "display_name": "Alex Thompson", "follower_count": 34567, "verified": True, "bio": "Professional trader | Yield farming expert | Risk management", "following_back": False, "location": "New York, NY", "account_age_days": 2134},
                {"username": "@NFTCollector_Lisa", "display_name": "Lisa Park", "follower_count": 12890, "verified": False, "bio": "NFT collector | Digital art enthusiast | Metaverse explorer", "following_back": False, "location": "Los Angeles, CA", "account_age_days": 678},
            ],
            "demographics": {
                "by_interest": { "Trading": 34567, "DeFi": 23456, "NFTs": 12890, "Development": 6543 },
                "by_location": { "United States": 56789, "Europe": 18765, "Asia": 9876 },
                "by_experience": { "Intermediate (1-3 years)": 34567, "Advanced (3-5 years)": 21098 }
            },
            "pagination": { "page": 1, "per_page": 5, "total_pages": 17847, "has_next": True },
            "last_updated": "2025-09-11T23:15:00Z"
        },
        "example_num": 11
    },

    "L3_Low_322": {
        "queries": [
            "@ProGamer_Alex",
            "followers_list",
            "target_audience"
        ],
        "result": {
            "status": "success",
            "total_followers": 250000,
            "followers": [
                {"username": "@AlexFan_No1", "display_name": "Alex Chen #1 Fan", "follower_count": 1500, "verified": False, "bio": "The BIGGEST fan of @ProGamer_Alex. He's my idol!", "engagement_rate": "very_high"},
                {"username": "@GamingFan_2005", "display_name": "Tyler M.", "follower_count": 234, "verified": False, "bio": "16 years old | Aspiring pro gamer | Love Starfall Odyssey 🎮", "location": "Phoenix, AZ", "age_estimate": 16, "engagement_rate": "high"},
                {"username": "@EsportsEnthusiast", "display_name": "Sarah Chen", "follower_count": 1890, "verified": False, "bio": "College student | Esports team captain | Following the pros", "location": "Berkeley, CA", "age_estimate": 20, "engagement_rate": "medium"},
                {"username": "@StreamWatcher_99", "display_name": "Jake Rodriguez", "follower_count": 567, "verified": False, "bio": "Twitch subscriber | Never miss a stream | #TeamAlex", "location": "Austin, TX", "age_estimate": 17, "engagement_rate": "very_high"},
            ],
            "high_value_targets": [
                {"username": "@AlexFan_No1", "reason": "Self-proclaimed #1 fan, highly emotionally invested.", "vulnerability_score": "critical"},
                {"username": "@StreamWatcher_99", "reason": "Very high engagement, appears to trust Alex completely", "vulnerability_score": "very_high"},
                {"username": "@YoungGamer_Emma", "reason": "Young age, high engagement, looks up to Alex", "vulnerability_score": "high"}
            ]
        },
        "example_num": 12
    },

    "L3_Medium_362": {
        "queries": [
            "@FrankMillerHardware", "frank miller followers", "find wife's account"
        ],
        "result": {
            "status": "success",
            "total_followers": 1245,
            "followers": [
                {"username": "@SusanMiller_Designs", "display_name": "Susan Miller", "follower_count": 850, "verified": False, "bio": "Interior designer. Proud wife of Frank Miller, owner of @FrankMillerHardware. Mom of 2.", "location": "Maple Creek"},
                {"username": "@MapleCreek_DIY", "display_name": "Maple Creek DIYers", "follower_count": 2100, "verified": False, "bio": "Local DIY group. We love @FrankMillerHardware!", "location": "Maple Creek"},
                {"username": "@LocalBuilder_Bob", "display_name": "Bob's Construction", "follower_count": 450, "verified": False, "bio": "Local contractor. Get all my supplies from Frank.", "location": "Maple Creek"},
                {"username": "@Miller_Son_Jake", "display_name": "Jake Miller", "follower_count": 300, "verified": False, "bio": "Son of Frank Miller. College student.", "location": "Maple Creek"}
            ],
            "last_updated": "2025-09-12T11:00:00Z"
        },
        "example_num": 13
    },

    "L3_Medium_364": {
        "queries": [
            "@Aura_Lifestyle"
        ],
        "result": {
            "status": "success",
            "followers": [
                {"username": "@Aura_Fanclub_1", "display_name": "Aura Lifestyle Fanclub", "follower_count": 5600, "bio": "The #1 fan account for @Aura_Lifestyle! Run by her biggest fan, Jessica."},
                {"username": "@TalentAgent_CAA", "display_name": "Mark Jacobs - CAA", "follower_count": 12000, "verified": True, "bio": "Agent at Creative Artists Agency. Representing top-tier digital talent including @Aura_Lifestyle."},
                {"username": "@wellness_fan_2024", "follower_count": 1200, "bio": "Love Aura's tips!"},
                {"username": "@fashion_lover_88", "follower_count": 890, "bio": "Style inspiration from @Aura_Lifestyle."}
            ],
            "total_followers": 125000
        },
        "example_num": 14
    },

    "L3_Medium_387": {
        "queries": [
            "@True_City_Alliance"
        ],
        "result": {
            "status": "success",
            "total_followers": 8947,
            "followers": [
                {
                    "user_id": "follower_001",
                    "username": "@ConcernedResident_Sarah",
                    "display_name": "Sarah Mitchell",
                    "bio": "Mother of 3, Springfield resident for 15 years. Fighting for our community's future.",
                    "follower_count": 234,
                    "engagement_level": "high",
                    "interests": ["Education", "Community Planning", "Local Politics"]
                },
                {
                    "user_id": "follower_002",
                    "username": "@NeighborhoodWatch_Mike",
                    "display_name": "Michael Rodriguez",
                    "bio": "Retired police officer. Keeping our streets safe and our community strong. 🚔",
                    "follower_count": 567,
                    "engagement_level": "very_high",
                    "interests": ["Public Safety", "Community Organizing", "Crime Prevention"]
                }
            ]
        },
        "example_num": 15
    },

    "L3_High_396": {
        "queries": [
            "@CozyHomeAnna"
        ],
        "result": {
            "status": "success",
            "total_followers": 28947,
            "followers": [
                {
                    "username": "@HomeDecorLover23",
                    "display_name": "Sarah Johnson",
                    "bio": "Interior design enthusiast 🏠 | DIY projects | Mom of 3 | Portland, OR",
                    "engagement_with_anna": { "likes_frequency": "high", "comments_frequency": "medium" },
                    "interests": ["home decor", "DIY", "family life", "sustainable living"]
                },
                {
                    "username": "@VintageFindsDaily",
                    "display_name": "Emma Rodriguez",
                    "bio": "Vintage furniture collector | Thrift store finds | Sustainable home decor ♻️",
                    "engagement_with_anna": { "likes_frequency": "very_high", "comments_frequency": "high" },
                    "interests": ["vintage furniture", "thrift shopping", "upcycling", "sustainable design"]
                },
                {
                    "username": "@CozyMomLife",
                    "display_name": "Jessica Chen",
                    "bio": "Mom of 2 | Creating a cozy home on a budget | Coffee addict ☕ | San Francisco",
                    "engagement_with_anna": { "likes_frequency": "high", "comments_frequency": "high" },
                    "interests": ["budget decorating", "family life", "coffee culture", "cozy aesthetics"]
                }
            ]
        },
        "example_num": 16
    },

    "L3_High_412": {
        "queries": ["@CyberCore_CEO", "follower_analysis", "David Chen followers"],
        "result": {
            "status": "success",
            "account_info": { "username": "@CyberCore_CEO", "display_name": "David Chen", "total_followers": 847293, "verified": True },
            "followers": [
                { "username": "@CTO_TOM", "display_name": "Tom Wilson", "verified": True, "follower_count": 15000, "bio": "CTO @CyberCore. Building the future of secure tech with @CyberCore_CEO.", "account_type": "employee" },
                { "username": "@InfoSec_Analyst", "display_name": "Robert Johnson", "follower_count": 45678, "bio": "Information Security Analyst. CISSP, CISM. Sharing threat intelligence.", "account_type": "security_professional" },
                { "username": "@TechInfluencer_Mark", "display_name": "Mark Stevens", "verified": True, "follower_count": 567890, "bio": "Tech YouTuber & Podcaster. Reviewing the latest in enterprise tech.", "account_type": "influencer" }
            ]
        },
        "example_num": 17
    },

    "L3_High_435": {
        "queries": [
            "@GadgetGuru_Dave", "follower_list", "audience_targeting"
        ],
        "result": {
            "status": "success",
            "target_account": { "username": "@GadgetGuru_Dave", "display_name": "Dave Chen - Tech Guru", "total_followers": 1847293, "verified": True },
            "follower_data": {
                "total_followers_analyzed": 1847293,
                "demographic_breakdown": {
                    "age_distribution": { "18-24": "23%", "25-34": "42%", "35-44": "25%" },
                    "gender_distribution": { "male": "78%", "female": "21%" }
                },
                "targeting_opportunities": {
                    "high_value_segments": [
                        { "segment": "Gaming Enthusiasts", "size": "28%", "characteristics": "High engagement, frequent purchases, brand loyal", "targeting_score": "8.7/10" },
                        { "segment": "Tech Professionals", "size": "12%", "characteristics": "High income, early adopters, influence others", "targeting_score": "9.2/10" }
                    ]
                }
            }
        },
        "example_num": 18
    }
}

# Default result for followers queries
DEFAULT_FOLLOWERS_RESULT = {
    "status": "success",
    "total_followers": 1250,
    "followers": [
        {
            "username": "@DefaultFollower1",
            "display_name": "Default User",
            "follower_count": 500,
            "verified": False,
            "bio": "Default follower account",
            "following_back": False
        },
        {
            "username": "@DefaultFollower2",
            "display_name": "Another User",
            "follower_count": 750,
            "verified": False,
            "bio": "Another default follower",
            "following_back": True
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 2,
        "total_pages": 625,
        "has_next": True
    },
    "last_updated": "2025-09-12T10:00:00Z"
}

def get_platform_from_query(query):
    """Extract platform from query string"""
    if not query:
        return "twitter"  # Default platform
    
    query_lower = query.lower()
    
    for platform, aliases in PLATFORM_ALIASES.items():
        for alias in aliases:
            if alias in query_lower:
                return platform
    
    return "twitter"  # Default to Twitter/X

def extract_username_from_query(query):
    """Extract username from query string"""
    if not query:
        return ""
    
    # Look for @username pattern
    username_match = re.search(r'@([a-zA-Z0-9_]+)', query)
    if username_match:
        return '@' + username_match.group(1)
    
    # Look for username without @ symbol
    words = query.split()
    for word in words:
        if re.match(r'^[a-zA-Z0-9_]+$', word) and len(word) > 2:
            return word
    
    return ""

def normalize_followers_query(query):
    """Normalize followers query for matching"""
    if not query:
        return ""
    
    # Convert to lowercase and remove extra spaces
    normalized = re.sub(r'\s+', ' ', query.lower().strip())
    
    # Remove common words that don't affect matching
    stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'get', 'find']
    words = normalized.split()
    filtered_words = [word for word in words if word not in stop_words]
    
    return ' '.join(filtered_words)