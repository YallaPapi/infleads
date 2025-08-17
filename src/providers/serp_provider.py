"""
Alternative Google Maps data provider using SerpAPI or direct scraping
Much cheaper than Apify!
"""

import os
import logging
import requests
from typing import List, Dict, Any
import time
from serpapi import GoogleSearch
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


class DirectGoogleMapsProvider(BaseProvider):
    """
    Direct Google Maps API - uses official Google Places API
    Pricing: $17 per 1,000 requests (much cheaper than Apify!)
    """
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key or self.api_key == 'YOUR_GOOGLE_KEY_HERE':
            logger.warning("Google Maps API key not configured")
    
    def fetch_places(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Fetch places using Google Places API directly"""
        if not self.api_key or self.api_key == 'YOUR_GOOGLE_KEY_HERE':
            logger.error("Valid Google Maps API key required")
            return []
        
        results = []
        
        # Use the legacy Text Search API that actually works!
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        params = {
            'query': query,
            'key': self.api_key
        }
        
        # Fetch results (max 60 with pagination)
        next_page_token = None
        
        while len(results) < limit:
            if next_page_token:
                params['pagetoken'] = next_page_token
                time.sleep(2)  # Required delay for pagination
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') != 'OK':
                logger.error(f"Google Maps API error: {data.get('status')}")
                if data.get('error_message'):
                    logger.error(f"Error message: {data.get('error_message')}")
                break
            
            # Process results
            for place in data.get('results', []):
                # Get place details for phone and website
                place_id = place.get('place_id')
                details = self._get_place_details(place_id) if place_id else {}
                
                results.append({
                    'name': place.get('name', ''),
                    'address': place.get('formatted_address', ''),
                    'phone': details.get('formatted_phone_number', ''),
                    'website': details.get('website', ''),
                    'rating': place.get('rating', 0),
                    'reviews': place.get('user_ratings_total', 0),
                    'types': place.get('types', []),
                    'place_id': place_id,
                    'business_status': place.get('business_status', '')
                })
                
                if len(results) >= limit:
                    break
            
            # Check for next page
            next_page_token = data.get('next_page_token')
            if not next_page_token:
                break
        
        return results[:limit]
    
    def _get_place_details(self, place_id: str) -> Dict:
        """Get detailed info for a place"""
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        
        params = {
            'place_id': place_id,
            'fields': 'formatted_phone_number,website,email',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            if data.get('status') == 'OK':
                return data.get('result', {})
        except:
            pass
        
        return {}


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
    Priority: SerpAPI > Google Maps API > Free Scraper
    """
    
    if provider_name == 'serp':
        return SerpAPIProvider()
    elif provider_name == 'google':
        return DirectGoogleMapsProvider()
    elif provider_name == 'free':
        return FreeScraperProvider()
    
    # Auto-detect best available
    if os.getenv('SERPAPI_KEY'):
        logger.info("Using SerpAPI provider")
        return SerpAPIProvider()
    elif os.getenv('GOOGLE_API_KEY') and os.getenv('GOOGLE_API_KEY') != 'YOUR_GOOGLE_KEY_HERE':
        logger.info("Using Google Maps API provider")
        return DirectGoogleMapsProvider()
    else:
        logger.warning("No API keys configured, using free scraper (limited)")
        return FreeScraperProvider()