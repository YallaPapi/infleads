"""
OpenStreetMap Overpass API Provider
Free business data from OpenStreetMap using Overpass API
"""

import requests
import logging
from typing import List, Dict, Optional, Tuple
import time
import re
from urllib.parse import quote
from .base import BaseProvider

logger = logging.getLogger(__name__)

class OpenStreetMapProvider(BaseProvider):
    """
    OpenStreetMap provider using Overpass API for business data
    Completely free, no API keys required
    """
    
    def __init__(self):
        self.base_url = 'https://overpass-api.de/api/interpreter'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'R27LeadsAgent/1.0 (Business Directory)'
        })
        self.rate_limit_delay = 2.5  # Increase delay to avoid 429 rate limiting errors
        self.last_request_time = 0
    
    def fetch_places(self, query: str, limit: int = 25) -> List[Dict]:
        """
        BaseProvider interface method - fetches places from OpenStreetMap
        
        Args:
            query: Search query like "coffee shops in Austin" 
            limit: Maximum number of results
            
        Returns:
            List of normalized business dictionaries
        """
        logger.info(f"OpenStreetMapProvider.fetch_places: query='{query}', limit={limit}")
        print(f"OSM DEBUG: Processing query='{query}'")
        
        # Parse location from query if present
        location = None
        if ' in ' in query:
            parts = query.split(' in ', 1)
            business_type = parts[0].strip()
            location = parts[1].strip()
            clean_query = business_type
            logger.debug(f"Parsed combined query: keyword='{business_type}', location='{location}'")
        else:
            clean_query = query
            location = "unknown"
            logger.debug(f"No location separator found, using query as keyword: '{clean_query}'")
            
        results = self.search_businesses(clean_query, location, limit)
        
        # Set search metadata for each result
        for result in results:
            result['search_keyword'] = clean_query
            result['search_location'] = location if location else "unknown"
            result['full_query'] = query
        
        logger.info(f"OpenStreetMapProvider returning {len(results)} results")
        return results
        
    def search_businesses(self, query: str, location: str = None, limit: int = 50) -> List[Dict]:
        """
        Search for businesses using OpenStreetMap Overpass API
        
        Args:
            query: Search query (e.g., "restaurants", "lawyers", "coffee shops")
            location: Location to search in (e.g., "New York, NY", "Las Vegas")
            limit: Maximum number of results
            
        Returns:
            List of normalized business data dictionaries
        """
        try:
            # Parse query and location
            search_term, search_location = self._parse_query(query, location)
            
            if not search_location:
                logger.warning("No location specified for OpenStreetMap search")
                return []
            
            # Get bounding box for location
            bbox = self._get_location_bbox(search_location)
            if not bbox:
                logger.warning(f"Could not determine bounding box for location: {search_location}")
                return []
            
            # Convert search term to OSM amenity/shop tags
            osm_tags = self._convert_to_osm_tags(search_term)
            if not osm_tags:
                logger.warning(f"Could not map search term to OSM tags: {search_term}")
                return []
            
            # Build and execute Overpass query
            overpass_query = self._build_overpass_query(osm_tags, bbox, limit)
            results = self._execute_overpass_query(overpass_query)
            
            if not results:
                return []
            
            # Normalize results
            businesses = []
            for element in results.get('elements', []):
                normalized = self._normalize_business(element)
                if normalized:
                    businesses.append(normalized)
            
            logger.info(f"OpenStreetMap search returned {len(businesses)} businesses for '{query}' in '{search_location}'")
            return businesses[:limit]
            
        except Exception as e:
            logger.error(f"OpenStreetMap search failed for '{query}': {e}")
            return []
    
    def _parse_query(self, query: str, location: str = None) -> Tuple[str, str]:
        """Parse search query to extract business type and location"""
        search_term = query.lower().strip()
        search_location = location
        
        # Try to extract location from query if not provided
        if not search_location and ' in ' in query:
            parts = query.split(' in ', 1)
            search_term = parts[0].strip().lower()
            search_location = parts[1].strip()
        
        return search_term, search_location
    
    def _convert_to_osm_tags(self, search_term: str) -> Optional[str]:
        """
        Convert search term to OpenStreetMap amenity/shop tags
        
        Returns:
            String of OSM tag filters for Overpass query
        """
        # Mapping of common search terms to OSM amenity/shop tags
        tag_mappings = {
            # Food & Drink
            'restaurant': 'amenity~"restaurant"',
            'restaurants': 'amenity~"restaurant"',
            'cafe': 'amenity~"cafe"',
            'coffee': 'amenity~"cafe"',
            'coffee shop': 'amenity~"cafe"',
            'bar': 'amenity~"bar"',
            'bars': 'amenity~"bar"',
            'pub': 'amenity~"pub"',
            'fast food': 'amenity~"fast_food"',
            'pizza': 'amenity~"restaurant"',  # Remove 'and' syntax which causes parse errors
            
            # Professional Services
            'lawyer': 'office~"lawyer"',
            'lawyers': 'office~"lawyer"',
            'attorney': 'office~"lawyer"',
            'law firm': 'office~"lawyer"',
            'dentist': 'amenity~"dentist"',
            'doctor': 'amenity~"doctors"',
            'medical': 'amenity~"clinic"',  # Simplify to avoid regex issues
            'accountant': 'office~"accountant"',
            'real estate': 'office~"estate_agent"',
            'insurance': 'office~"insurance"',
            
            # Retail
            'shop': 'shop',
            'store': 'shop',
            'grocery': 'shop~"supermarket"',  # Simplify regex pattern
            'pharmacy': 'amenity~"pharmacy"',
            'gas station': 'amenity~"fuel"',
            'bank': 'amenity~"bank"',
            'atm': 'amenity~"atm"',
            
            # Services
            'hotel': 'tourism~"hotel"',
            'gym': 'leisure~"fitness_centre"',
            'fitness': 'leisure~"fitness_centre"',
            'salon': 'shop~"hairdresser"',  # Simplify regex pattern
            'beauty': 'shop~"beauty"',  # Simplify regex pattern
            'auto repair': 'shop~"car_repair"',
            'mechanic': 'shop~"car_repair"',
            
            # Entertainment
            'cinema': 'amenity~"cinema"',
            'theater': 'amenity~"theatre"',
            'museum': 'tourism~"museum"',
        }
        
        # Try exact match first
        if search_term in tag_mappings:
            return tag_mappings[search_term]
        
        # Try partial matches
        for term, tags in tag_mappings.items():
            if term in search_term or search_term in term:
                return tags
        
        # Fallback: try as shop category
        return f'shop~"{search_term}"'
    
    def _get_location_bbox(self, location: str) -> Optional[Tuple[float, float, float, float]]:
        """
        Get bounding box coordinates for a location using Nominatim
        
        Returns:
            Tuple of (south, west, north, east) coordinates
        """
        try:
            # Use Nominatim API to get bounding box
            nominatim_url = 'https://nominatim.openstreetmap.org/search'
            params = {
                'q': location,
                'format': 'json',
                'limit': 1,
                'extratags': 1,
                'addressdetails': 1
            }
            
            headers = {'User-Agent': 'R27LeadsAgent/1.0 (Business Directory)'}
            response = requests.get(nominatim_url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    result = data[0]
                    if 'boundingbox' in result:
                        bbox = result['boundingbox']
                        # Nominatim returns [south, north, west, east]
                        # Overpass expects [south, west, north, east]
                        return (float(bbox[0]), float(bbox[2]), float(bbox[1]), float(bbox[3]))
            
            # Fallback: Use approximate bounding box for major cities
            city_bboxes = {
                'new york': (40.4774, -74.2591, 40.9176, -73.7004),
                'los angeles': (33.7037, -118.6681, 34.3373, -118.1553),
                'chicago': (41.6444, -87.9402, 42.0230, -87.5242),
                'las vegas': (36.0395, -115.3183, 36.2946, -114.9962),
                'miami': (25.7617, -80.4337, 25.8557, -80.1918),
                'san francisco': (37.7049, -122.5280, 37.8114, -122.3549),
            }
            
            location_lower = location.lower()
            for city, bbox in city_bboxes.items():
                if city in location_lower:
                    return bbox
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get bounding box for {location}: {e}")
            return None
    
    def _build_overpass_query(self, osm_tags: str, bbox: Tuple[float, float, float, float], limit: int) -> str:
        """
        Build Overpass API query string
        
        Args:
            osm_tags: OSM tag filters
            bbox: Bounding box (south, west, north, east)
            limit: Maximum results
            
        Returns:
            Overpass query string
        """
        south, west, north, east = bbox
        bbox_str = f"{south},{west},{north},{east}"
        
        # Build comprehensive query for nodes and ways
        query = f"""
        [out:json][timeout:25];
        (
          node[{osm_tags}]["name"]({bbox_str});
          way[{osm_tags}]["name"]({bbox_str});
          relation[{osm_tags}]["name"]({bbox_str});
        );
        out center meta {limit};
        """
        
        return query.strip()
    
    def _execute_overpass_query(self, query: str) -> Optional[Dict]:
        """Execute Overpass API query with rate limiting"""
        try:
            # Implement rate limiting to avoid 429 errors
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
            
            response = self.session.post(
                self.base_url,
                data=query,
                headers={'Content-Type': 'text/plain'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limited by Overpass API (429), backing off")
                time.sleep(5)  # Back off for 5 seconds on rate limit
                return None
            else:
                logger.error(f"Overpass API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Overpass API request timed out")
            return None
        except Exception as e:
            logger.error(f"Overpass API request failed: {e}")
            return None
    
    def _normalize_business(self, element: Dict) -> Optional[Dict]:
        """
        Normalize OSM business data to standard format
        
        Args:
            element: OSM element from Overpass API
            
        Returns:
            Normalized business dictionary or None if invalid
        """
        try:
            tags = element.get('tags', {})
            name = tags.get('name', '').strip()
            
            if not name:
                return None
            
            # Extract coordinates
            if element['type'] == 'node':
                latitude = element.get('lat')
                longitude = element.get('lon')
            elif 'center' in element:
                latitude = element['center'].get('lat')
                longitude = element['center'].get('lon')
            else:
                latitude = longitude = None
            
            # Build address from OSM tags with fallbacks
            address_parts = []
            if tags.get('addr:housenumber'):
                address_parts.append(tags['addr:housenumber'])
            if tags.get('addr:street'):
                address_parts.append(tags['addr:street'])
            if tags.get('addr:city'):
                address_parts.append(tags['addr:city'])
            if tags.get('addr:state'):
                address_parts.append(tags['addr:state'])
            if tags.get('addr:postcode'):
                address_parts.append(tags['addr:postcode'])
            
            # If no structured address, try alternative fields
            if not address_parts:
                if tags.get('addr:full'):
                    address_parts.append(tags['addr:full'])
                elif tags.get('address'):
                    address_parts.append(tags['address'])
            
            # If still no address, use coordinates as fallback
            if not address_parts and latitude and longitude:
                address = f"Near {latitude:.4f}, {longitude:.4f}"
            else:
                address = ', '.join(address_parts) if address_parts else 'Address not available'
            
            # Extract contact info
            phone = tags.get('phone', '').strip()
            website = tags.get('website', '').strip()
            if not website:
                website = tags.get('contact:website', '').strip()
            
            # Extract business type
            business_type = 'Business'
            if tags.get('amenity'):
                business_type = tags['amenity'].replace('_', ' ').title()
            elif tags.get('shop'):
                business_type = tags['shop'].replace('_', ' ').title() + ' Shop'
            elif tags.get('office'):
                business_type = tags['office'].replace('_', ' ').title() + ' Office'
            elif tags.get('tourism'):
                business_type = tags['tourism'].replace('_', ' ').title()
            
            # Create normalized business data in expected format
            normalized = {
                # Required fields for data normalizer
                'name': name,
                'address': address,
                'phone': phone if phone else 'NA',
                'email': 'NA',  # OSM doesn't have emails
                'website': website if website else 'NA',
                'rating': 0,  # OSM doesn't have ratings
                'reviews': 0,  # OSM doesn't have review counts
                'types': [business_type],
                'place_id': f"osm_{element.get('type', 'unknown')}_{element.get('id', '0')}",
                'business_status': 'OPERATIONAL',  # Assume operational
                'source': 'openstreetmap',
                'search_keyword': 'business',  # Will be set by calling code
                'search_location': 'unknown',  # Will be set by calling code
                'full_query': 'business search',  # Will be set by calling code
                
                # Additional OSM-specific fields
                'latitude': latitude,
                'longitude': longitude,
                'business_type': business_type,
                'osm_id': element.get('id'),
                'osm_type': element.get('type'),
                'osm_amenity': tags.get('amenity'),
                'osm_shop': tags.get('shop'),
                'osm_office': tags.get('office'),
                'osm_opening_hours': tags.get('opening_hours'),
                'osm_cuisine': tags.get('cuisine'),
                'osm_wheelchair': tags.get('wheelchair'),
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Failed to normalize OSM business data: {e}")
            return None
    
    def test_connection(self) -> Dict:
        """
        Test the OpenStreetMap API connection
        
        Returns:
            dict: Test results with status and message
        """
        try:
            # Make a minimal test query
            test_query = """
            [out:json][timeout:10];
            (
              node["amenity"~"cafe"]["name"](37.7749,-122.4194,37.7849,-122.4094);
            );
            out 1;
            """
            
            response = self.session.post(
                self.base_url,
                data=test_query,
                headers={'Content-Type': 'text/plain'},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                element_count = len(data.get('elements', []))
                
                return {
                    'success': True,
                    'message': f'OpenStreetMap API connection successful. Found {element_count} test result(s).',
                    'setup_required': False
                }
            else:
                return {
                    'success': False,
                    'message': f'OpenStreetMap API returned status {response.status_code}',
                    'setup_required': False
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'OpenStreetMap API test failed: {str(e)}',
                'setup_required': False
            }
    
    def is_configured(self) -> bool:
        """OpenStreetMap is always available (no API key required)"""
        return True