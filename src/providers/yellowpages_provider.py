"""
Yellow Pages Scraper Provider
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import time
import re

logger = logging.getLogger(__name__)

class YellowPagesProvider:
    """
    Yellow Pages scraper for additional business data
    """
    
    def __init__(self):
        self.base_url = 'https://www.yellowpages.com'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
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
            
            # Build search URL
            params = {
                'search_terms': search_term,
                'geo_location_terms': location or 'USA'
            }
            
            response = self.session.get(
                f'{self.base_url}/search',
                params=params
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                businesses = self._parse_search_results(soup, limit)
                logger.info(f"Yellow Pages returned {len(businesses)} businesses")
                return businesses
            else:
                logger.error(f"Yellow Pages error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error scraping Yellow Pages: {e}")
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