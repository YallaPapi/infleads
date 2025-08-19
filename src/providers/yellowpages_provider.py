"""
Yellow Pages Scraper Provider
Now using ScrapeGraph AI for intelligent web scraping with LLM-powered data extraction
"""

import logging
import time
import re
import os
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

try:
    from scrapegraphai.graphs import SmartScraperGraph
    SCRAPEGRAPH_AVAILABLE = True
except ImportError:
    SCRAPEGRAPH_AVAILABLE = False

# Always import requests for fallback
import requests

logger = logging.getLogger(__name__)

class YellowPagesProvider:
    """
    Yellow Pages scraper for additional business data
    Now uses ScrapeGraph AI for intelligent web scraping with LLM-powered data extraction
    """
    
    def __init__(self):
        self.base_url = 'https://www.yellowpages.com'
        self.use_scrapegraph = SCRAPEGRAPH_AVAILABLE
        
        # Check for OpenAI API key (ScrapeGraph needs an LLM)
        self.openai_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_key and self.use_scrapegraph:
            logger.warning("No OPENAI_API_KEY found. ScrapeGraph AI requires an LLM provider. Falling back to requests.")
            self.use_scrapegraph = False
        
        if not self.use_scrapegraph:
            # Fallback to regular requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            })
        else:
            logger.info("Using ScrapeGraph AI for Yellow Pages scraping (intelligent LLM-powered extraction)")
            self.session = None
        
        # Add delay between requests to avoid rate limiting
        self.request_delay = 1
    
    def search_businesses(self, query: str, location: str = None, limit: int = 20) -> List[Dict]:
        """
        Search for businesses on Yellow Pages
        """
        try:
            # Parse query
            if not location and ' in ' in query:
                parts = query.split(' in ')
                search_term = parts[0]
                location = parts[1] if len(parts) > 1 else ''
            else:
                search_term = query
            
            if self.use_scrapegraph:
                # Use ScrapeGraph AI for intelligent extraction
                businesses = self._search_with_scrapegraph(search_term, location or 'USA', limit)
                if businesses:
                    return businesses
                else:
                    # If ScrapeGraph fails, fall back to requests
                    logger.info("ScrapeGraph AI failed, trying requests fallback...")
                    params = {
                        'search_terms': search_term,
                        'geo_location_terms': location or 'USA'
                    }
                    return self._search_with_requests(params, limit)
            else:
                # Fallback to regular requests
                params = {
                    'search_terms': search_term,
                    'geo_location_terms': location or 'USA'
                }
                return self._search_with_requests(params, limit)
                
        except Exception as e:
            logger.error(f"Error scraping Yellow Pages: {e}")
            return []
    
    def _search_with_scrapegraph(self, search_term: str, location: str, limit: int) -> List[Dict]:
        """
        Search using ScrapeGraph AI (intelligent LLM-powered extraction)
        """
        try:
            # Build the search URL
            encoded_term = quote_plus(search_term)
            encoded_location = quote_plus(location)
            url = f"{self.base_url}/search?search_terms={encoded_term}&geo_location_terms={encoded_location}"
            
            logger.info(f"Yellow Pages ScrapeGraph AI request: {url}")
            
            # FIXED: Simple graph configuration to avoid parameter conflicts
            graph_config = {
                "llm": {
                    "api_key": self.openai_key,
                    "model": "openai/gpt-4o-mini",
                },
                "verbose": False,
                "headless": True  # ONLY this parameter - no conflicts
            }
            
            # Define what we want to extract
            prompt = f"""
            Extract business information from this Yellow Pages search results page for "{search_term}" in "{location}".
            For each business listing, get:
            - Business name
            - Phone number  
            - Address (full address)
            - Website (if available, set to null if not found)
            - Business categories/types (list)
            - Rating (if available, as a number, otherwise null)
            - Years in business (if mentioned, as a number, otherwise null)
            
            IMPORTANT: Return valid JSON format. Use null instead of NA for missing values.
            Return the data as a structured list of businesses. Extract up to {limit} businesses.
            """
            
            # Create and run the smart scraper
            smart_scraper_graph = SmartScraperGraph(
                prompt=prompt,
                source=url,
                config=graph_config
            )
            
            result = smart_scraper_graph.run()
            logger.info(f"ScrapeGraph AI raw result type: {type(result)}")
            
            # Convert the result to our expected format
            businesses = self._convert_scrapegraph_result(result)
            
            logger.info(f"Yellow Pages (ScrapeGraph AI) returned {len(businesses)} businesses")
            return businesses
            
        except Exception as e:
            logger.error(f"ScrapeGraph AI error: {e}")
            return []
    
    def _convert_scrapegraph_result(self, result) -> List[Dict]:
        """
        Convert ScrapeGraph AI result to our expected format
        """
        businesses = []
        
        logger.info(f"Converting ScrapeGraph result: {type(result)}")
        logger.debug(f"Raw result content: {result}")
        
        try:
            # Handle different result formats that ScrapeGraph AI might return
            if isinstance(result, list):
                data = result
            elif isinstance(result, dict):
                # Check if it has a 'content' key (ScrapeGraph AI format)
                if 'content' in result:
                    content = result['content']
                    if isinstance(content, list):
                        data = content
                    else:
                        logger.warning(f"Content is not a list: {type(content)}")
                        return []
                # Check if it has other standard keys
                elif 'businesses' in result:
                    data = result['businesses']
                elif 'results' in result:
                    data = result['results']
                elif 'data' in result:
                    data = result['data']
                else:
                    # If it's a dict but no obvious key, try to extract values that look like lists
                    for value in result.values():
                        if isinstance(value, list) and len(value) > 0:
                            data = value
                            break
                    else:
                        data = [result]  # Treat the dict as a single business
            else:
                logger.warning(f"Unexpected ScrapeGraph result format: {type(result)}")
                return []
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                    
                # Extract and normalize the fields - handle ScrapeGraph AI's field naming
                business = {
                    'name': str(item.get('Business name', item.get('business_name', item.get('name', '')))).strip(),
                    'phone': str(item.get('Phone number', item.get('phone_number', item.get('phone', '')))).strip(),
                    'address': str(item.get('Address', item.get('address', ''))).strip(),
                    'website': str(item.get('Website', item.get('website', ''))).strip(),
                    'rating': 0,
                    'reviews': 0,  # Use 'reviews' to match system standard (gets mapped to ReviewCount in CSV)
                    'categories': [],
                    'types': [],
                    'place_id': '',
                    'business_status': 'OPERATIONAL',
                    'source': 'yellowpages',
                    'years_in_business': None
                }
                
                # Handle rating
                if 'rating' in item:
                    try:
                        business['rating'] = float(item['rating'])
                    except (ValueError, TypeError):
                        business['rating'] = 0
                
                # Handle categories/business types - check for ScrapeGraph AI format
                categories = item.get('Business categories/types', item.get('business_categories', item.get('categories', item.get('types', []))))
                if categories:
                    if isinstance(categories, list):
                        business['categories'] = [str(cat).strip() for cat in categories]
                    elif isinstance(categories, str):
                        business['categories'] = [categories.strip()]
                    business['types'] = business['categories']
                
                # Handle years in business - check for ScrapeGraph AI format
                years_field = item.get('Years in business', item.get('years_in_business', None))
                if years_field:
                    try:
                        # Extract number from strings like "16 Years"
                        if isinstance(years_field, str):
                            import re
                            match = re.search(r'(\d+)', years_field)
                            if match:
                                business['years_in_business'] = int(match.group(1))
                        else:
                            business['years_in_business'] = int(years_field)
                    except (ValueError, TypeError):
                        business['years_in_business'] = None
                
                # Generate place_id
                name_part = business['name'].replace(' ', '_')[:20]
                addr_part = business['address'][:20] if business['address'] else ''
                business['place_id'] = f"yp_{name_part}_{addr_part}"
                
                # Only add businesses with at least a name
                if business['name']:
                    businesses.append(business)
            
        except Exception as e:
            logger.error(f"Error converting ScrapeGraph result: {e}")
            logger.debug(f"Raw result: {result}")
        
        logger.info(f"Converted {len(businesses)} businesses from ScrapeGraph result")
        return businesses
    
    def _search_with_requests(self, params: dict, limit: int) -> List[Dict]:
        """
        Search using regular requests (fallback)
        """
        # Add delay to avoid rate limiting
        time.sleep(self.request_delay)
        
        response = self.session.get(
            f'{self.base_url}/search',
            params=params,
            timeout=10
        )
        
        logger.info(f"Yellow Pages request: {response.url}")
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            businesses = self._parse_search_results(soup, limit)
            logger.info(f"Yellow Pages returned {len(businesses)} businesses")
            return businesses
        elif response.status_code == 403:
            logger.error(f"Yellow Pages blocked request (403 Forbidden). This is likely due to anti-bot detection.")
            logger.error("Suggestion: Install ScrapeGraph AI with 'pip install scrapegraphai' and set OPENAI_API_KEY for intelligent scraping.")
            return []
        elif response.status_code == 429:
            logger.error(f"Yellow Pages rate limit exceeded (429). Waiting before retry...")
            time.sleep(5)
            return []
        else:
            logger.error(f"Yellow Pages error: {response.status_code}")
            logger.debug(f"Response content: {response.text[:500]}...")
            return []
    
    def _parse_search_results(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """
        Parse search results from Yellow Pages HTML
        """
        businesses = []
        results = soup.find_all('div', class_='result', limit=limit)
        
        for result in results:
            try:
                business = self._extract_business_info(result)
                if business:
                    businesses.append(business)
            except Exception as e:
                logger.debug(f"Error parsing result: {e}")
                continue
        
        return businesses
    
    def _extract_business_info(self, result_div) -> Optional[Dict]:
        """
        Extract business information from a result div
        """
        try:
            # Business name
            name_elem = result_div.find('a', class_='business-name')
            if not name_elem:
                return None
            name = name_elem.get_text(strip=True)
            
            # Phone
            phone = ''
            phone_elem = result_div.find('div', class_='phones')
            if phone_elem:
                phone = phone_elem.get_text(strip=True)
            
            # Address
            address = ''
            address_elem = result_div.find('div', class_='street-address')
            locality_elem = result_div.find('div', class_='locality')
            
            if address_elem:
                address = address_elem.get_text(strip=True)
            if locality_elem:
                address += ', ' + locality_elem.get_text(strip=True)
            
            # Website
            website = ''
            website_elem = result_div.find('a', class_='track-visit-website')
            if website_elem:
                website = website_elem.get('href', '')
            
            # Rating
            rating = 0
            rating_elem = result_div.find('div', class_='ratings')
            if rating_elem:
                rating_match = re.search(r'(\d+\.?\d*)', rating_elem.get('class', [''])[1])
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Categories
            categories = []
            cat_elem = result_div.find('div', class_='categories')
            if cat_elem:
                cat_links = cat_elem.find_all('a')
                categories = [link.get_text(strip=True) for link in cat_links]
            
            # Years in business
            years_in_business = None
            info_elem = result_div.find('div', class_='years-in-business')
            if info_elem:
                years_match = re.search(r'(\d+)', info_elem.get_text())
                if years_match:
                    years_in_business = int(years_match.group(1))
            
            return {
                'name': name,
                'address': address,
                'phone': phone,
                'website': website,
                'rating': rating,
                'reviews': 0,  # Yellow Pages doesn't show review count in search
                'categories': categories,
                'types': categories,
                'place_id': f"yp_{name.replace(' ', '_')}_{address[:20]}",
                'business_status': 'OPERATIONAL',
                'source': 'yellowpages',
                'years_in_business': years_in_business
            }
            
        except Exception as e:
            logger.debug(f"Error extracting business info: {e}")
            return None
    
    def get_business_details(self, business_url: str) -> Optional[Dict]:
        """
        Get detailed information about a specific business
        """
        try:
            response = self.session.get(business_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                details = {}
                
                # Extract additional details
                # Business hours
                hours_elem = soup.find('div', class_='hours')
                if hours_elem:
                    details['hours'] = hours_elem.get_text(strip=True)
                
                # Email
                email_elem = soup.find('a', class_='email-business')
                if email_elem:
                    details['email'] = email_elem.get('href', '').replace('mailto:', '')
                
                # Description
                desc_elem = soup.find('dd', class_='general-info')
                if desc_elem:
                    details['description'] = desc_elem.get_text(strip=True)
                
                # Payment methods
                payment_elem = soup.find('dd', class_='payment')
                if payment_elem:
                    details['payment_methods'] = payment_elem.get_text(strip=True)
                
                return details
            else:
                logger.error(f"Error getting business details: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching business details: {e}")
            return None
    
    def fetch_places(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Compatibility method for provider interface
        """
        return self.search_businesses(query, limit=limit)