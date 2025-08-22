"""
Multi-provider cascade to get high-volume results by combining multiple sources
"""

import os
import logging
import re
from typing import List, Dict, Any, Set
from .base import BaseProvider
# Google providers removed - using OpenStreetMap and free providers only
from .hybrid_scraper import HybridGoogleScraper
from .pure_scraper import PureWebScraper
from .openstreetmap_provider import OpenStreetMapProvider

# Import BotasaurusProvider with error handling
try:
    from .botasaurus_provider import BotasaurusProvider
    BOTASAURUS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"BotasaurusProvider not available: {e}")
    BotasaurusProvider = None
    BOTASAURUS_AVAILABLE = False

logger = logging.getLogger(__name__)

class MultiProvider(BaseProvider):
    """
    Combines multiple providers to get high-volume results
    Uses OpenStreetMap + Hybrid Scraper + Pure Scraper (all FREE)
    """
    
    def __init__(self, enable_botasaurus: bool = True, use_cache: bool = True):
        """
        Initialize MultiProvider with configurable provider selection
        
        Args:
            enable_botasaurus: Enable BotasaurusProvider if available
            use_cache: Enable caching for BotasaurusProvider
        """
        self.providers = []
        
        # 🛡️ COST PROTECTION: Use FREE providers first!
        # Only use expensive Google APIs as a last resort
        
        # 1. PREMIUM: BotasaurusProvider (most advanced, if available)
        if enable_botasaurus and BOTASAURUS_AVAILABLE:
            try:
                botasaurus_provider = BotasaurusProvider(use_cache=use_cache)
                self.providers.append(('BotasaurusProvider', botasaurus_provider))
                logger.info("✨ BotasaurusProvider enabled - Advanced browser automation with contact extraction")
            except Exception as e:
                logger.warning(f"Failed to initialize BotasaurusProvider: {e}")
        
        # 2. FREE: OpenStreetMap (most reliable free option)
        self.providers.append(('OpenStreetMap', OpenStreetMapProvider()))
        
        # 3. FREE: Pure web scraper (no API costs)
        self.providers.append(('PureScraper', PureWebScraper()))
        
        # 4. FREE: Hybrid scraper (uses free geocoding only)  
        self.providers.append(('HybridScraper', HybridGoogleScraper()))
        
        # Provider summary
        provider_names = [name for name, _ in self.providers]
        logger.info(f"🛡️ MultiProvider initialized with {len(self.providers)} providers:")
        logger.info(f"📋 Active providers: {', '.join(provider_names)}")
        
        if 'BotasaurusProvider' in provider_names:
            logger.info("🚀 Advanced mode: BotasaurusProvider will handle complex searches with contact extraction")
        else:
            logger.info("⚡ Standard mode: Using free scrapers only")
        
        logger.info("💡 All providers are cost-free - no API charges!")
    
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
    
    def _validate_query_format(self, query: str) -> Dict[str, Any]:
        """Validate and provide details about query format for debugging"""
        validation = {
            'original_query': query,
            'has_location_separator': ' in ' in query.lower(),
            'format_type': 'unknown',
            'is_valid': False,
            'issues': []
        }
        
        if not query or not query.strip():
            validation['issues'].append('Empty or whitespace-only query')
            return validation
        
        if validation['has_location_separator']:
            parts = query.lower().split(' in ', 1)
            if len(parts) == 2:
                keyword, location = parts
                if keyword.strip() and location.strip():
                    validation['format_type'] = 'combined'
                    validation['is_valid'] = True
                else:
                    validation['issues'].append('Empty keyword or location in combined format')
            else:
                validation['issues'].append('Malformed combined format')
        else:
            # Assume it's just a keyword or location
            validation['format_type'] = 'keyword_only'
            validation['is_valid'] = True
            validation['issues'].append('No location specified - results may be limited')
        
        return validation
    
    def fetch_places(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Fetch places using multiple providers until we reach the limit
        Handles both "restaurants in New York" and separate query/location formats
        """
        logger.info(f"Multi-provider fetch: query='{query}', target={limit}")
        print(f"MULTI-PROVIDER DEBUG: Processing query='{query}' with limit={limit}")
        
        # Validate query format and log details
        validation = self._validate_query_format(query)
        logger.info(f"Query validation: format_type={validation['format_type']}, is_valid={validation['is_valid']}")
        if validation['issues']:
            logger.warning(f"Query issues: {', '.join(validation['issues'])}")
        
        # Parse query once so we can annotate results consistently
        q_parts = self._split_query(query)
        search_keyword = q_parts.get('keyword', '').strip()
        search_location = self._clean_city(q_parts.get('location', '').strip())
        
        logger.info(f"Query parsing result: keyword='{search_keyword}', location='{search_location}'")
        
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
                
                # Pass the original query to the provider - let each provider handle parsing
                # This ensures consistent behavior regardless of query format
                logger.debug(f"Calling {provider_name}.fetch_places('{query}', {request_limit})")
                results = provider.fetch_places(query, request_limit)
                
                logger.debug(f"{provider_name} returned {len(results)} raw results")
                unique_results = []
                
                # Deduplicate by business name and ensure consistent metadata
                for result in results:
                    name = result.get('name', '').strip().lower()
                    if name and name not in seen_names:
                        seen_names.add(name)
                        result['source'] = provider_name  # Tag with source
                        
                        # Ensure consistent query metadata across all providers
                        # Override any inconsistent values from sub-providers
                        result['full_query'] = query
                        result['search_keyword'] = search_keyword if search_keyword else result.get('search_keyword', 'business')
                        result['search_location'] = search_location if search_location else result.get('search_location', 'unknown')
                        
                        logger.debug(f"Adding result: {name} from {provider_name} (keyword: {result['search_keyword']}, location: {result['search_location']})")
                        unique_results.append(result)
                        
                        if len(all_results) + len(unique_results) >= limit:
                            unique_results = unique_results[:limit - len(all_results)]
                            break
                
                all_results.extend(unique_results)
                remaining_limit = limit - len(all_results)
                
                logger.info(f"{provider_name} contributed {len(unique_results)} unique results (total: {len(all_results)}/{limit})")
                
                # Log sample of results for debugging
                if unique_results and logger.isEnabledFor(logging.DEBUG):
                    sample_result = unique_results[0]
                    logger.debug(f"Sample result from {provider_name}: name='{sample_result.get('name', 'N/A')}', keyword='{sample_result.get('search_keyword', 'N/A')}', location='{sample_result.get('search_location', 'N/A')}'")
                
                # If we got very few results from this provider, try the next one
                if len(unique_results) < 5 and remaining_limit > 10:
                    continue
                    
            except Exception as e:
                logger.error(f"Provider {provider_name} failed with query '{query}': {e}")
                # Log more details for debugging
                logger.debug(f"Provider {provider_name} error details:", exc_info=True)
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
