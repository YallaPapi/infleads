"""
Lead data providers for R27 Infinite AI Leads Agent
"""

from .base import BaseProvider
# from .apify_provider import ApifyProvider  # FUCK APIFY - removed
from .serp_provider import get_maps_provider
# Google providers removed - using free providers only
from .hybrid_scraper import HybridGoogleScraper
from .multi_provider import MultiProvider
from .yellowpages_provider import YellowPagesProvider
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
    
    # Google providers removed - return MultiProvider instead
    if provider_name in ['google', 'google_new']:
        logger.warning("Google providers removed - using free MultiProvider instead")
        return MultiProvider()
    
    # Hybrid scraper as fallback
    if provider_name == 'hybrid':
        return HybridGoogleScraper()
    
    # Yellow Pages provider
    if provider_name == 'yellowpages':
        return YellowPagesProvider()
    
    return get_maps_provider(provider_name)