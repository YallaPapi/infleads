"""
Multi-provider cascade to get high-volume results by combining multiple sources
"""

import os
import logging
from typing import List, Dict, Any, Set
from .base import BaseProvider
# Google providers removed - using OpenStreetMap and free providers only
from .hybrid_scraper import HybridGoogleScraper
from .pure_scraper import PureWebScraper
from .openstreetmap_provider import OpenStreetMapProvider

logger = logging.getLogger(__name__)

class MultiProvider(BaseProvider):
    """
    Combines multiple providers to get high-volume results
    Uses OpenStreetMap + Hybrid Scraper + Pure Scraper (all FREE)
    """
    
    def __init__(self):
        self.providers = []
        
        # 🛡️ COST PROTECTION: Use FREE providers first!
        # Only use expensive Google APIs as a last resort
        
        # 1. FREE: OpenStreetMap (most reliable free option)
        self.providers.append(('OpenStreetMap', OpenStreetMapProvider()))
        
        # 2. FREE: Pure web scraper (no API costs)
        self.providers.append(('PureScraper', PureWebScraper()))
        
        # 3. FREE: Hybrid scraper (uses free geocoding only)  
        self.providers.append(('HybridScraper', HybridGoogleScraper()))
        
        # Using only FREE providers - no Google API costs
        logger.info("🛡️ Using only FREE providers - no API costs!")
        logger.info("💡 OpenStreetMap, PureScraper, and HybridScraper are all free")
        
        logger.info(f"MultiProviderCascade initialized with {len(self.providers)} providers")
    
    def fetch_places(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Fetch places using multiple providers until we reach the limit
        """
        logger.info(f"Multi-provider fetch: query='{query}', target={limit}")
        
        all_results = []
        seen_names = set()
        remaining_limit = limit
        
        for provider_name, provider in self.providers:
            if remaining_limit <= 0:
                break
                
            try:
                logger.info(f"Trying {provider_name} for {remaining_limit} more results...")
                
                # Request more from each provider to account for duplicates
                request_limit = min(remaining_limit * 2, 100)  # Request 2x to account for deduplication
                
                results = provider.fetch_places(query, request_limit)
                unique_results = []
                
                # Deduplicate by business name
                for result in results:
                    name = result.get('name', '').strip().lower()
                    if name and name not in seen_names:
                        seen_names.add(name)
                        result['source'] = provider_name  # Tag with source
                        unique_results.append(result)
                        
                        if len(all_results) + len(unique_results) >= limit:
                            unique_results = unique_results[:limit - len(all_results)]
                            break
                
                all_results.extend(unique_results)
                remaining_limit = limit - len(all_results)
                
                logger.info(f"{provider_name} contributed {len(unique_results)} unique results (total: {len(all_results)}/{limit})")
                
                # If we got very few results from this provider, try the next one
                if len(unique_results) < 5 and remaining_limit > 10:
                    continue
                    
            except Exception as e:
                logger.error(f"Provider {provider_name} failed: {e}")
                continue
        
        logger.info(f"Multi-provider cascade completed: {len(all_results)} total results from {len([p for p, _ in self.providers])} providers")
        return all_results[:limit]
    
    def _normalize_business_name(self, name: str) -> str:
        """Normalize business name for deduplication"""
        if not name:
            return ""
        
        # Remove common suffixes/prefixes for better matching
        name = name.lower().strip()
        
        # Remove common business suffixes
        suffixes = ['llc', 'inc', 'corp', 'ltd', 'co', 'company', '&amp;', 'and', 'the']
        words = name.split()
        filtered_words = [w for w in words if w not in suffixes]
        
        return ' '.join(filtered_words) if filtered_words else name
