"""
Multi-provider cascade to get high-volume results by combining multiple sources
"""

import os
import logging
import re
from typing import List, Dict, Any, Set
from .base import BaseProvider
from .serp_provider import DirectGoogleMapsProvider
from .google_places_new import GooglePlacesNewProvider
from .hybrid_scraper import HybridGoogleScraper
from .pure_scraper import PureWebScraper

logger = logging.getLogger(__name__)

class MultiProvider(BaseProvider):
    """
    Combines multiple providers to get high-volume results
    Uses Google Maps API + Google Places + Hybrid Scraper + Pure Scraper
    """
    
    def __init__(self):
        self.providers = []
        
        # Add providers in order of quality/reliability
        if os.getenv('GOOGLE_API_KEY'):
            self.providers.append(('DirectGoogleMaps', DirectGoogleMapsProvider()))
            self.providers.append(('GooglePlacesNew', GooglePlacesNewProvider()))
        
        self.providers.append(('HybridScraper', HybridGoogleScraper()))
        self.providers.append(('PureScraper', PureWebScraper()))
        
        logger.info(f"MultiProviderCascade initialized with {len(self.providers)} providers")
    
    def _split_query(self, query: str) -> Dict[str, str]:
        """Split an incoming query into keyword and location parts.
        Returns dict with 'keyword' and 'location' strings (un-empty strings or '').
        Case-insensitive on the separator ' in '.
        """
        keyword = query.strip()
        location = ''
        parts = re.split(r"\s+in\s+", query, flags=re.IGNORECASE, maxsplit=1)
        if len(parts) == 2:
            keyword = parts[0].strip()
            location = parts[1].strip()
        return {"keyword": keyword, "location": location}
    
    def _clean_city(self, text: str) -> str:
        """Clean a location string down to a city-like value.
        - Take first chunk before '|'
        - If chunk contains ' in ', use the part after it
        - Collapse whitespace and Title-Case
        """
        if not text:
            return ''
        chunk = re.split(r"\|", str(text))[0].strip()
        # if someone passed phrases like 'restaurant in dallas'
        parts = re.split(r"\s+in\s+", chunk, flags=re.IGNORECASE, maxsplit=1)
        if len(parts) == 2:
            chunk = parts[1].strip()
        chunk = re.sub(r"\s+", " ", chunk)
        return chunk.title()
    
    def fetch_places(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Fetch places using multiple providers until we reach the limit
        """
        logger.info(f"Multi-provider fetch: query='{query}', target={limit}")
        
        # Parse query once so we can annotate results consistently
        q_parts = self._split_query(query)
        search_keyword = q_parts.get('keyword', '').strip()
        search_location = self._clean_city(q_parts.get('location', '').strip())
        
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
                        # Annotate with query metadata if not present
                        result.setdefault('full_query', query)
                        if not result.get('search_keyword'):
                            result['search_keyword'] = search_keyword
                        if not result.get('search_location'):
                            result['search_location'] = search_location
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
