"""
Lead data providers for R27 Infinite AI Leads Agent
"""

from .base import BaseProvider
# from .apify_provider import ApifyProvider  # FUCK APIFY - removed
from .serp_provider import get_maps_provider, DirectGoogleMapsProvider
from .google_places_new import GooglePlacesNewProvider
from .hybrid_scraper import HybridGoogleScraper
from .multi_provider import MultiProvider
import os
import logging

logger = logging.getLogger(__name__)

def get_provider(provider_name: str = 'auto') -> BaseProvider:
    """Factory function to get the appropriate provider"""
    # NO MORE APIFY - using alternatives
    
    # Use the multi-provider cascade for high-volume requests
    if provider_name == 'auto':
        logger.info("DEBUG: Returning MultiProvider for 'auto' request")
        return MultiProvider()
    
    # Use the working Google Maps Legacy API by default!
    if provider_name == 'google' and os.getenv('GOOGLE_API_KEY'):
        return DirectGoogleMapsProvider()
    
    # Try the new Google Places API if specifically requested
    if provider_name == 'google_new' and os.getenv('GOOGLE_API_KEY'):
        return GooglePlacesNewProvider()
    
    # Hybrid scraper as fallback
    if provider_name == 'hybrid':
        return HybridGoogleScraper()
    
    return get_maps_provider(provider_name)