"""
Alternative Google Maps data provider using SerpAPI or direct scraping
Much cheaper than Apify!
"""

import os
import logging
import requests
from typing import List, Dict, Any
import time
# from serpapi import Client  # Not needed for DirectGoogleMapsProvider
import json
from .base import BaseProvider

logger = logging.getLogger(__name__)

class SerpAPIProvider(BaseProvider):
    """
    Uses SerpAPI for Google Maps data - $50/month for 5,000 searches
    That's $0.01 per search vs Apify's insane pricing
    """
    
    def __init__(self):
        self.api_key = os.getenv('SERPAPI_KEY')
        if not self.api_key:
            logger.warning("SERPAPI_KEY not found, will try alternative methods")
    
    def fetch_places(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Fetch places using SerpAPI"""
        if not self.api_key:
            logger.error("No SERPAPI_KEY configured")
            return []
        
        results = []
        
        # SerpAPI search
        params = {
            "engine": "google_maps",
            "q": query,
            "type": "search",
            "api_key": self.api_key,
            "num": min(limit, 20)  # Max 20 per request
        }
        
        search = GoogleSearch(params)
        data = search.get_dict()
        
        # Extract local results
        for place in data.get("local_results", []):
            results.append({
                'name': place.get('title', ''),
                'address': place.get('address', ''),
                'phone': place.get('phone', ''),
                'website': place.get('website', ''),
                'rating': place.get('rating', 0),
                'reviews': place.get('reviews', 0),
                'type': place.get('type', ''),
                'place_id': place.get('place_id', ''),
                'data_cid': place.get('data_cid', ''),
            })
        
        return results[:limit]


# DirectGoogleMapsProvider has been removed - using OpenStreetMap instead


class FreeScraperProvider(BaseProvider):
    """
    FREE alternative - scrapes Google Maps directly (use with caution)
    No API costs but may get rate limited
    """
    
    def fetch_places(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Scrape Google Maps search results page directly
        This is free but may get blocked if used too much
        """
        import urllib.parse
        from bs4 import BeautifulSoup
        
        results = []
        
        # Build Google Maps search URL
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/maps/search/{encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            # This is a simplified example - real implementation would need
            # to handle JavaScript rendering, pagination, etc.
            response = requests.get(url, headers=headers)
            
            # Parse the page (would need Selenium for full functionality)
            # This is just a placeholder for the concept
            logger.warning("Free scraping requires Selenium for full functionality")
            
            # For now, return empty list
            # A full implementation would use Selenium to render JS
            return []
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return []


def get_maps_provider(provider_name: str = None):
    """
    Get the best available Maps provider
    Priority: SerpAPI > Free Scraper
    """
    
    if provider_name == 'serp':
        return SerpAPIProvider()
    elif provider_name == 'free':
        return FreeScraperProvider()
    
    # Auto-detect best available
    if os.getenv('SERPAPI_KEY'):
        logger.info("Using SerpAPI provider")
        return SerpAPIProvider()
    else:
        logger.warning("No API keys configured, using free scraper (limited)")
        return FreeScraperProvider()