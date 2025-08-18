"""
Yellow Pages API Provider using hosted service
Uses the free hosted Yellow Pages API from GitHub
"""

import requests
import logging
from typing import List, Dict, Optional, Tuple
import time
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)

class YellowPagesAPIProvider:
    """
    Yellow Pages provider using the hosted API service
    Free hosted API that wraps Yellow Pages scraping
    """
    
    def __init__(self):
        self.base_url = 'http://hrushis-yellow-pages-end-api.herokuapp.com'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'R27LeadsAgent/1.0 (Business Directory)',
            'Accept': 'application/json'
        })
        self.rate_limit_delay = 2.0  # 2 seconds between requests to be respectful
        
    def search_businesses(self, query: str, location: str = None, limit: int = 50) -> List[Dict]:
        """
        Search for businesses using Yellow Pages hosted API
        
        Args:
            query: Search query (e.g., "restaurants", "lawyers", "dentists")
            location: Location to search in (e.g., "New York", "Las Vegas", "Miami")
            limit: Maximum number of results
            
        Returns:
            List of normalized business data dictionaries
        """
        try:
            # Parse query and location
            search_term, search_location = self._parse_query(query, location)
            
            if not search_location:
                logger.warning("No location specified for Yellow Pages search")
                return []
            
            # Clean and format search terms for the API
            clean_term = self._clean_search_term(search_term)
            clean_location = self._clean_location(search_location)
            
            if not clean_term or not clean_location:
                logger.warning(f"Invalid search parameters: term='{clean_term}', location='{clean_location}'")
                return []
            
            # Calculate pages needed (API returns ~30 results per page)
            results_per_page = 30
            pages_needed = min(5, (limit // results_per_page) + 1)  # Max 5 pages
            
            all_businesses = []
            
            for page in range(1, pages_needed + 1):
                try:
                    # Build API URL
                    api_url = f"{self.base_url}/{clean_term}/{clean_location}/{page}"
                    
                    logger.info(f"Fetching Yellow Pages data from: {api_url}")
                    
                    # Make API request
                    response = self.session.get(api_url, timeout=30)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            
                            # Handle different response formats
                            if isinstance(data, list):
                                businesses = data
                            elif isinstance(data, dict) and 'businesses' in data:
                                businesses = data['businesses']
                            elif isinstance(data, dict) and 'results' in data:
                                businesses = data['results']
                            else:
                                logger.warning(f"Unexpected API response format: {type(data)}")
                                businesses = []
                            
                            if not businesses:
                                logger.info(f"No more results on page {page}, stopping pagination")
                                break
                            
                            # Normalize and add businesses
                            for business in businesses:
                                normalized = self._normalize_business(business)
                                if normalized:
                                    all_businesses.append(normalized)
                            
                            logger.info(f"Yellow Pages page {page}: found {len(businesses)} businesses")
                            
                            # Stop if we have enough results
                            if len(all_businesses) >= limit:
                                break
                            
                            # Rate limiting between pages
                            if page < pages_needed:
                                time.sleep(self.rate_limit_delay)
                                
                        except ValueError as e:
                            logger.error(f"Failed to parse JSON from Yellow Pages API: {e}")
                            break
                            
                    elif response.status_code == 404:
                        logger.warning(f"Yellow Pages API returned 404 for '{clean_term}' in '{clean_location}'")
                        break
                    else:
                        logger.error(f"Yellow Pages API error: {response.status_code} - {response.text[:200]}")
                        break
                        
                except requests.exceptions.Timeout:
                    logger.error(f"Yellow Pages API timeout on page {page}")
                    break
                except requests.exceptions.ConnectionError:
                    logger.error(f"Cannot connect to Yellow Pages API on page {page}")
                    break
                except Exception as e:
                    logger.error(f"Yellow Pages API request failed on page {page}: {e}")
                    break
            
            logger.info(f"Yellow Pages search returned {len(all_businesses)} businesses for '{query}' in '{search_location}'")
            return all_businesses[:limit]
            
        except Exception as e:
            logger.error(f"Yellow Pages search failed for '{query}': {e}")
            return []
    
    def _parse_query(self, query: str, location: str = None) -> Tuple[str, str]:
        """Parse search query to extract business type and location"""
        search_term = query.strip()
        search_location = location
        
        # Try to extract location from query if not provided
        if not search_location and ' in ' in query:
            parts = query.split(' in ', 1)
            search_term = parts[0].strip()
            search_location = parts[1].strip()
        
        return search_term, search_location
    
    def _clean_search_term(self, term: str) -> str:
        """
        Clean and format search term for Yellow Pages API
        
        Args:
            term: Raw search term
            
        Returns:
            Cleaned search term suitable for API
        """
        if not term:
            return ""
        
        # Convert to lowercase and replace spaces with hyphens
        clean_term = term.lower().strip()
        
        # Handle common business type variations
        term_mappings = {
            'attorneys': 'lawyers',
            'attorney': 'lawyers',
            'law firms': 'lawyers',
            'law firm': 'lawyers',
            'dental': 'dentists',
            'dental offices': 'dentists',
            'medical': 'doctors',
            'physicians': 'doctors',
            'cafes': 'restaurants',
            'coffee shops': 'restaurants',
            'coffee shop': 'restaurants',
            'auto repair': 'mechanics',
            'car repair': 'mechanics',
            'beauty salons': 'beauty-shops',
            'hair salons': 'beauty-shops',
            'real estate agents': 'real-estate',
            'realtors': 'real-estate',
        }
        
        # Apply mappings
        if clean_term in term_mappings:
            clean_term = term_mappings[clean_term]
        
        # Replace spaces with hyphens and remove special characters
        clean_term = re.sub(r'[^a-z0-9\s-]', '', clean_term)
        clean_term = re.sub(r'\s+', '-', clean_term)
        clean_term = re.sub(r'-+', '-', clean_term).strip('-')
        
        return clean_term
    
    def _clean_location(self, location: str) -> str:
        """
        Clean and format location for Yellow Pages API
        
        Args:
            location: Raw location string
            
        Returns:
            Cleaned location suitable for API
        """
        if not location:
            return ""
        
        # Remove common suffixes and clean
        clean_location = location.lower().strip()
        
        # Remove state/country suffixes and clean up
        clean_location = re.sub(r',?\s*(usa?|united states)$', '', clean_location, re.IGNORECASE)
        clean_location = re.sub(r',?\s*[a-z]{2}$', '', clean_location)  # Remove state abbreviations
        
        # Handle common city name variations
        location_mappings = {
            'new york city': 'new-york',
            'nyc': 'new-york',
            'la': 'los-angeles',
            'san fran': 'san-francisco',
            'sf': 'san-francisco',
            'vegas': 'las-vegas',
            'miami beach': 'miami',
        }
        
        if clean_location in location_mappings:
            clean_location = location_mappings[clean_location]
        
        # Replace spaces with hyphens and remove special characters
        clean_location = re.sub(r'[^a-z0-9\s-]', '', clean_location)
        clean_location = re.sub(r'\s+', '-', clean_location)
        clean_location = re.sub(r'-+', '-', clean_location).strip('-')
        
        return clean_location
    
    def _normalize_business(self, business: Dict) -> Optional[Dict]:
        """
        Normalize Yellow Pages business data to standard format
        
        Args:
            business: Raw business data from Yellow Pages API
            
        Returns:
            Normalized business dictionary or None if invalid
        """
        try:
            # Handle different possible field names from the API
            name = business.get('name') or business.get('title') or business.get('business_name', '').strip()
            
            if not name or name.lower() in ['', 'n/a', 'not available']:
                return None
            
            # Extract address
            address = business.get('address') or business.get('location') or business.get('full_address', '').strip()
            if not address or address.lower() in ['', 'n/a', 'not available']:
                address = 'Address not available'
            
            # Extract phone
            phone = business.get('phone') or business.get('phone_number') or business.get('telephone', '').strip()
            if not phone or phone.lower() in ['', 'n/a', 'not available']:
                phone = 'Not available'
            else:
                # Clean phone number
                phone = re.sub(r'[^\d\-\(\)\+\s\.]', '', phone)
            
            # Extract website
            website = business.get('website') or business.get('url') or business.get('web', '').strip()
            if not website or website.lower() in ['', 'n/a', 'not available', 'none']:
                website = 'Not available'
            elif not website.startswith(('http://', 'https://')):
                website = f"http://{website}"
            
            # Extract business type/category
            business_type = business.get('category') or business.get('categories') or business.get('type', 'Business')
            if isinstance(business_type, list) and business_type:
                business_type = business_type[0]
            business_type = str(business_type).strip() or 'Business'
            
            # Extract rating if available
            rating = business.get('rating') or business.get('stars')
            if rating:
                try:
                    rating = float(rating)
                except (ValueError, TypeError):
                    rating = None
            
            # Create normalized business data
            normalized = {
                'name': name,
                'address': address,
                'phone': phone,
                'website': website,
                'business_type': business_type,
                'data_source': 'Yellow Pages',
                # Yellow Pages specific fields
                'yp_rating': rating,
                'yp_years_in_business': business.get('years_in_business'),
                'yp_categories': business.get('categories') if isinstance(business.get('categories'), list) else None,
                'yp_more_info': business.get('more_info') or business.get('details'),
                'yp_status': business.get('status'),
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Failed to normalize Yellow Pages business data: {e}")
            return None
    
    def test_connection(self) -> Dict:
        """
        Test the Yellow Pages API connection
        
        Returns:
            dict: Test results with status and message
        """
        try:
            # Make a minimal test request
            test_url = f"{self.base_url}/dentists/new-york/1"
            
            response = self.session.get(test_url, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        count = len(data)
                    elif isinstance(data, dict):
                        count = len(data.get('businesses', data.get('results', [])))
                    else:
                        count = 0
                    
                    return {
                        'success': True,
                        'message': f'Yellow Pages API connection successful. Found {count} test result(s).',
                        'setup_required': False
                    }
                except ValueError:
                    return {
                        'success': False,
                        'message': 'Yellow Pages API returned invalid JSON',
                        'setup_required': False
                    }
            else:
                return {
                    'success': False,
                    'message': f'Yellow Pages API returned status {response.status_code}',
                    'setup_required': False
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Yellow Pages API test failed: {str(e)}',
                'setup_required': False
            }
    
    def is_configured(self) -> bool:
        """Yellow Pages API is always available (no API key required)"""
        return True