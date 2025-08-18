#!/usr/bin/env python3
"""
Rate Limiting and IP Protection Configuration
"""

import os
from typing import List

class RateLimitConfig:
    """Configuration for rate limiting and IP protection"""
    
    # Rate limiting delays (seconds)
    MIN_DELAY = float(os.getenv('MIN_SCRAPE_DELAY', '1.0'))
    MAX_DELAY = float(os.getenv('MAX_SCRAPE_DELAY', '3.0'))
    
    # Request limits per hour
    HOURLY_LIMIT = int(os.getenv('HOURLY_REQUEST_LIMIT', '1000'))
    
    # User agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    # Proxy configuration (optional)
    PROXY_LIST = []  # Add your proxy servers here if needed
    
    @classmethod
    def should_use_proxy(cls) -> bool:
        """Check if proxy should be used based on request volume"""
        return len(cls.PROXY_LIST) > 0 and os.getenv('USE_PROXY', 'false').lower() == 'true'

# Usage example for your .env file:
"""
# Rate limiting settings
MIN_SCRAPE_DELAY=2.0
MAX_SCRAPE_DELAY=5.0
HOURLY_REQUEST_LIMIT=500
USE_PROXY=false

# For high-volume scraping, consider:
# USE_PROXY=true
# HOURLY_REQUEST_LIMIT=100
"""
