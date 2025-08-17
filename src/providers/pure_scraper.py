#!/usr/bin/env python3
"""
Pure Web Scraper - NO API KEYS REQUIRED!
Scrapes business data directly from web search results.
"""

import requests
import re
import json
import logging
from typing import List, Dict, Any
from urllib.parse import quote, urlparse
import time
from bs4 import BeautifulSoup
import random

logger = logging.getLogger(__name__)

class PureWebScraper:
    """
    Scrapes business data from various search engines
    No API keys required - completely FREE!
    """
    
    def __init__(self):
        self.session = requests.Session()
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self._set_random_user_agent()
    
    def _set_random_user_agent(self):
        """Set a random user agent"""
        ua = random.choice(self.user_agents)
        self.session.headers.update({
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def fetch_places(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Main entry point - fetches business data"""
        
        logger.info(f"Pure web scraping for: {query}")
        results = []
        
        # Try multiple search engines
        
        # 1. DuckDuckGo (no rate limiting, good for businesses)
        duckduckgo_results = self._scrape_duckduckgo(query, limit)
        results.extend(duckduckgo_results)
        
        # 2. Bing Maps (often has good local data)
        if len(results) < limit:
            bing_results = self._scrape_bing_maps(query, limit - len(results))
            results.extend(bing_results)
        
        # 3. Yellow Pages style sites
        if len(results) < limit:
            yp_results = self._scrape_yellow_pages(query, limit - len(results))
            results.extend(yp_results)
        
        # 4. OpenStreetMap Nominatim (free, no API key)
        if len(results) < limit:
            osm_results = self._scrape_openstreetmap(query, limit - len(results))
            results.extend(osm_results)
        
        # Deduplicate results
        seen = set()
        unique_results = []
        for r in results:
            name = r.get('name', '')
            if name and name not in seen:
                seen.add(name)
                unique_results.append(r)
        
        if unique_results:
            logger.info(f"Pure scraper found {len(unique_results)} unique businesses")
        else:
            logger.warning("No results from pure scraping, using sample data")
            unique_results = self._get_sample_data(query, limit)
        
        return unique_results[:limit]
    
    def _scrape_duckduckgo(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape DuckDuckGo for business info"""
        
        results = []
        
        try:
            # DuckDuckGo doesn't rate limit as aggressively
            encoded_query = quote(query + " business phone address")
            url = f"https://duckduckgo.com/html/?q={encoded_query}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for result snippets
                for result in soup.find_all('div', class_='result__body')[:limit]:
                    try:
                        title_elem = result.find('a', class_='result__a')
                        snippet_elem = result.find('a', class_='result__snippet')
                        
                        if title_elem:
                            name = title_elem.text.strip()
                            snippet = snippet_elem.text.strip() if snippet_elem else ''
                            
                            # Extract phone from snippet
                            phone_match = re.search(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', snippet)
                            phone = phone_match.group(0) if phone_match else ''
                            
                            # Extract address patterns
                            address = ''
                            # Look for street address pattern
                            addr_match = re.search(r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)', snippet, re.I)
                            if addr_match:
                                address = addr_match.group(0)
                            
                            results.append({
                                'name': name,
                                'address': address or 'Address not found',
                                'phone': phone,
                                'website': '',
                                'rating': 0,
                                'reviews': 0,
                                'source': 'duckduckgo'
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing DuckDuckGo result: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"DuckDuckGo scraping error: {e}")
        
        return results
    
    def _scrape_bing_maps(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape Bing Maps for business info"""
        
        results = []
        
        try:
            encoded_query = quote(query)
            url = f"https://www.bing.com/maps?q={encoded_query}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Look for JSON data in the response
                json_pattern = r'"businessListings":\s*\[(.*?)\]'
                match = re.search(json_pattern, response.text)
                
                if match:
                    try:
                        # Parse the JSON data
                        listings_str = '[' + match.group(1) + ']'
                        listings = json.loads(listings_str)
                        
                        for listing in listings[:limit]:
                            results.append({
                                'name': listing.get('name', ''),
                                'address': listing.get('address', ''),
                                'phone': listing.get('phone', ''),
                                'website': listing.get('website', ''),
                                'rating': listing.get('rating', 0),
                                'reviews': listing.get('reviewCount', 0),
                                'source': 'bing_maps'
                            })
                    except:
                        pass
                
                # Fallback: HTML parsing
                if not results:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Look for business cards
                    for card in soup.find_all('div', class_='b_entityTP')[:limit]:
                        try:
                            name = card.find('h2')
                            if name:
                                results.append({
                                    'name': name.text.strip(),
                                    'address': 'Search Bing Maps',
                                    'phone': '',
                                    'website': '',
                                    'rating': 0,
                                    'reviews': 0,
                                    'source': 'bing_maps'
                                })
                        except:
                            continue
        
        except Exception as e:
            logger.error(f"Bing Maps scraping error: {e}")
        
        return results
    
    def _scrape_yellow_pages(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape Yellow Pages style directories"""
        
        results = []
        
        # Extract business type and location
        business_type = 'business'
        location = 'USA'
        
        if ' in ' in query:
            parts = query.split(' in ')
            business_type = parts[0]
            location = parts[1]
        
        try:
            # Try YellowPages.com (US)
            encoded_type = quote(business_type)
            encoded_location = quote(location)
            url = f"https://www.yellowpages.com/search?search_terms={encoded_type}&geo_location_terms={encoded_location}"
            
            # Use a shorter timeout
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for business listings
                for listing in soup.find_all('div', class_='result')[:limit]:
                    try:
                        name_elem = listing.find('a', class_='business-name')
                        if name_elem:
                            name = name_elem.text.strip()
                            
                            # Get address
                            addr_elem = listing.find('div', class_='street-address')
                            locality_elem = listing.find('div', class_='locality')
                            address = ''
                            if addr_elem:
                                address = addr_elem.text.strip()
                            if locality_elem:
                                address += ' ' + locality_elem.text.strip()
                            
                            # Get phone
                            phone_elem = listing.find('div', class_='phones')
                            phone = phone_elem.text.strip() if phone_elem else ''
                            
                            results.append({
                                'name': name,
                                'address': address or 'Address not listed',
                                'phone': phone,
                                'website': '',
                                'rating': 0,
                                'reviews': 0,
                                'source': 'yellowpages'
                            })
                    except:
                        continue
        
        except Exception as e:
            logger.debug(f"Yellow Pages scraping failed: {e}")
        
        return results
    
    def _scrape_openstreetmap(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Use OpenStreetMap Nominatim for geocoding (free, no API key)"""
        
        results = []
        
        try:
            # Nominatim is free but requires a user agent
            headers = dict(self.session.headers)
            headers['User-Agent'] = 'R27LeadsAgent/1.0'
            
            encoded_query = quote(query)
            url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit={limit}&addressdetails=1"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for place in data:
                    # Extract business name from display name
                    display_name = place.get('display_name', '')
                    name_parts = display_name.split(',')[0:2]
                    name = name_parts[0] if name_parts else 'Business'
                    
                    # Build address from components
                    addr = place.get('address', {})
                    address_parts = []
                    if addr.get('house_number'):
                        address_parts.append(addr['house_number'])
                    if addr.get('road'):
                        address_parts.append(addr['road'])
                    if addr.get('city'):
                        address_parts.append(addr['city'])
                    elif addr.get('town'):
                        address_parts.append(addr['town'])
                    if addr.get('state'):
                        address_parts.append(addr['state'])
                    
                    address = ', '.join(address_parts) if address_parts else display_name
                    
                    results.append({
                        'name': name,
                        'address': address,
                        'phone': '',
                        'website': '',
                        'rating': 0,
                        'reviews': 0,
                        'latitude': place.get('lat'),
                        'longitude': place.get('lon'),
                        'source': 'openstreetmap'
                    })
        
        except Exception as e:
            logger.debug(f"OpenStreetMap scraping failed: {e}")
        
        return results
    
    def _get_sample_data(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Generate sample data as fallback"""
        
        business_type = 'business'
        location = 'USA'
        
        if ' in ' in query:
            parts = query.split(' in ')
            business_type = parts[0]
            location = parts[1]
        
        sample_data = []
        for i in range(min(limit, 25)):
            sample_data.append({
                'name': f"{business_type.title()} #{i+1}",
                'address': f"{100+i*10} Main Street, {location}",
                'phone': f"(555) {100+i:03d}-{1000+i:04d}",
                'website': f"www.{business_type.lower().replace(' ', '')}{i+1}.com",
                'rating': 4.0 + (i % 10) / 10,
                'reviews': 50 + i * 10,
                'source': 'sample_data'
            })
        
        return sample_data