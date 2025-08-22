#!/usr/bin/env python3
"""
BotasaurusProvider - Advanced lead generation using Botasaurus framework
Comprehensive browser automation with anti-detection and contact extraction
"""

import os
import logging
import re
import json
import time
import random
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse, quote
from pathlib import Path

try:
    from botasaurus import *
    from botasaurus.browser import Browser
    from botasaurus.request import Request
    from botasaurus_driver.browser_launcher import BrowserLauncher
    from botasaurus_proxy_authentication import add_proxy_to_driver
    import botasaurus_requests
except ImportError as e:
    logging.warning(f"Botasaurus not available: {e}")
    Browser = None

from .base import BaseProvider
from ..dorks_engine import DorksEngine

logger = logging.getLogger(__name__)


class ContactExtractor:
    """Utility class for extracting contact information from web pages"""
    
    def __init__(self):
        # Email patterns
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'[Ee]mail[\s]*:[\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'[Cc]ontact[\s]*@[\s]*([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
        ]
        
        # Phone patterns
        self.phone_patterns = [
            r'\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'(?:phone|tel|call)[\s]*:?[\s]*(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})',
            r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
            r'\+1[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}',
        ]
        
        # Social media patterns
        self.social_patterns = {
            'facebook': r'(?:facebook\.com|fb\.com)/([A-Za-z0-9._-]+)',
            'linkedin': r'linkedin\.com/(?:in|company)/([A-Za-z0-9._-]+)',
            'twitter': r'(?:twitter\.com|x\.com)/([A-Za-z0-9._-]+)',
            'instagram': r'instagram\.com/([A-Za-z0-9._-]+)',
            'youtube': r'youtube\.com/(?:channel|c|user)/([A-Za-z0-9._-]+)',
            'tiktok': r'tiktok\.com/@([A-Za-z0-9._-]+)',
        }
        
        # Website patterns
        self.website_patterns = [
            r'https?://(?:www\.)?([A-Za-z0-9.-]+\.[A-Za-z]{2,})',
            r'www\.([A-Za-z0-9.-]+\.[A-Za-z]{2,})',
            r'(?:website|site|web)[\s]*:[\s]*(https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
        ]
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        emails = set()
        for pattern in self.email_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if isinstance(matches[0], tuple) if matches else False:
                emails.update([match[0] if isinstance(match, tuple) else match for match in matches])
            else:
                emails.update(matches)
        
        # Filter out obvious false positives
        filtered_emails = []
        for email in emails:
            email = email.strip().lower()
            if (email and '@' in email and '.' in email and 
                not any(bad in email for bad in ['png', 'jpg', 'gif', 'css', 'js', 'example.com'])):
                filtered_emails.append(email)
        
        return list(filtered_emails)
    
    def extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        phones = set()
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Reconstruct phone number from tuple
                    phone = ''.join(match)
                    if len(phone) >= 10:
                        formatted_phone = f"({match[0]}) {match[1]}-{match[2]}"
                        phones.add(formatted_phone)
                else:
                    # Clean and format phone number
                    clean_phone = re.sub(r'[^\d]', '', match)
                    if len(clean_phone) >= 10:
                        phones.add(match.strip())
        
        return list(phones)
    
    def extract_social_media(self, text: str, page_url: str = None) -> Dict[str, str]:
        """Extract social media links from text"""
        social_links = {}
        
        for platform, pattern in self.social_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take the first valid match
                username = matches[0]
                if username and not any(skip in username.lower() for skip in ['home', 'login', 'signup']):
                    social_links[platform] = f"https://{platform}.com/{username}"
        
        return social_links
    
    def extract_websites(self, text: str) -> List[str]:
        """Extract website URLs from text"""
        websites = set()
        for pattern in self.website_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and '.' in match:
                    # Clean and format URL
                    url = match.strip()
                    if not url.startswith('http'):
                        url = f"https://{url}"
                    websites.add(url)
        
        return list(websites)


class CacheManager:
    """Intelligent caching system for scraped data"""
    
    def __init__(self, cache_dir: str = "cache", cache_duration_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_duration = timedelta(hours=cache_duration_hours)
    
    def _get_cache_key(self, query: str, search_type: str = "business") -> str:
        """Generate cache key from query"""
        content = f"{search_type}_{query.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get_cached_results(self, query: str, search_type: str = "business") -> Optional[List[Dict]]:
        """Get cached results if they exist and are fresh"""
        try:
            cache_key = self._get_cache_key(query, search_type)
            cache_path = self._get_cache_path(cache_key)
            
            if not cache_path.exists():
                return None
            
            # Check if cache is expired
            cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
            if cache_age > self.cache_duration:
                logger.debug(f"Cache expired for query: {query}")
                cache_path.unlink()  # Delete expired cache
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            logger.info(f"Using cached results for query: {query} ({len(cached_data)} results)")
            return cached_data
            
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None
    
    def cache_results(self, query: str, results: List[Dict], search_type: str = "business") -> None:
        """Cache search results"""
        try:
            cache_key = self._get_cache_key(query, search_type)
            cache_path = self._get_cache_path(cache_key)
            
            # Add cache metadata
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'search_type': search_type,
                'result_count': len(results),
                'results': results
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data['results'], f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cached {len(results)} results for query: {query}")
            
        except Exception as e:
            logger.warning(f"Error caching results: {e}")


class AntiDetectionManager:
    """Manages anti-detection features for web scraping"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        ]
        
        self.viewport_sizes = [
            (1920, 1080),
            (1366, 768),
            (1536, 864),
            (1440, 900),
            (1280, 720)
        ]
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(self.user_agents)
    
    def get_random_viewport(self) -> tuple:
        """Get a random viewport size"""
        return random.choice(self.viewport_sizes)
    
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """Add random delay between actions"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def simulate_human_behavior(self, driver) -> None:
        """Simulate human-like behavior"""
        try:
            # Random mouse movements
            driver.execute_script("""
                var event = new MouseEvent('mousemove', {
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight
                });
                document.dispatchEvent(event);
            """)
            
            # Random scroll
            scroll_y = random.randint(0, 500)
            driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            
            # Short delay
            self.random_delay(0.5, 1.5)
            
        except Exception as e:
            logger.debug(f"Error in human behavior simulation: {e}")


class BotasaurusProvider(BaseProvider):
    """
    Advanced lead generation provider using Botasaurus framework
    Features: Browser automation, anti-detection, contact extraction, caching
    """
    
    def __init__(self, use_cache: bool = True, cache_duration_hours: int = 24, 
                 enable_proxy: bool = False, proxy_list: List[str] = None):
        """
        Initialize BotasaurusProvider
        
        Args:
            use_cache: Enable intelligent caching
            cache_duration_hours: How long to cache results
            enable_proxy: Enable proxy rotation
            proxy_list: List of proxy servers
        """
        if Browser is None:
            raise ImportError("Botasaurus framework not available. Please install botasaurus package.")
        
        self.dorks_engine = DorksEngine()
        self.contact_extractor = ContactExtractor()
        self.anti_detection = AntiDetectionManager()
        
        # Cache management
        self.use_cache = use_cache
        if use_cache:
            cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'cache', 'botasaurus')
            self.cache_manager = CacheManager(cache_dir, cache_duration_hours)
        
        # Proxy configuration
        self.enable_proxy = enable_proxy
        self.proxy_list = proxy_list or []
        self.current_proxy_index = 0
        
        # Browser configuration
        self.browser_config = {
            'headless': True,
            'block_images': True,  # Faster loading
            'wait_for_complete_page_load': False,  # Don't wait for all resources
            'user_agent': self.anti_detection.get_random_user_agent(),
            'window_size': self.anti_detection.get_random_viewport(),
            'add_arguments': [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-javascript',  # Disable JS for faster loading when not needed
            ]
        }
        
        # Search configuration
        self.max_parallel_browsers = 3
        self.max_results_per_dork = 10
        self.max_pages_per_search = 5
        
        logger.info(f"BotasaurusProvider initialized - Cache: {use_cache}, Proxy: {enable_proxy}")
    
    def fetch_places(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Main entry point - fetch business leads using advanced scraping
        
        Args:
            query: Search query (e.g., "dentists in Miami")
            limit: Maximum number of results
            
        Returns:
            List of business lead dictionaries
        """
        logger.info(f"BotasaurusProvider.fetch_places: query='{query}', limit={limit}")
        
        # Check cache first
        if self.use_cache:
            cached_results = self.cache_manager.get_cached_results(query, "business_leads")
            if cached_results:
                return cached_results[:limit]
        
        # Parse query
        business_type, location = self._parse_query(query)
        if not business_type or not location:
            logger.warning(f"Could not parse query: {query}")
            return self._get_fallback_data(query, limit)
        
        # Generate search strategy
        search_strategy = self.dorks_engine.create_search_strategy(
            business_type, location, max_queries=15
        )
        
        all_results = []
        seen_businesses = set()
        
        try:
            # Execute multi-phase scraping
            
            # Phase 1: Primary business discovery
            primary_results = self._scrape_with_dorks(
                search_strategy['primary_business'][:5], limit // 2
            )
            all_results.extend(self._deduplicate_results(primary_results, seen_businesses))
            
            # Phase 2: Contact-focused searches if we need more results
            if len(all_results) < limit and search_strategy['contact_focused']:
                contact_results = self._scrape_with_dorks(
                    search_strategy['contact_focused'][:5], limit - len(all_results)
                )
                all_results.extend(self._deduplicate_results(contact_results, seen_businesses))
            
            # Phase 3: Enhanced contact extraction
            if all_results:
                all_results = self._enhance_contact_info(all_results[:limit])
            
            # Phase 4: Social media enrichment
            if len(all_results) < limit * 0.8:  # If we have less than 80% of desired results
                social_results = self._scrape_social_media(business_type, location, limit - len(all_results))
                all_results.extend(self._deduplicate_results(social_results, seen_businesses))
            
        except Exception as e:
            logger.error(f"Error in fetch_places: {e}", exc_info=True)
            if not all_results:
                all_results = self._get_fallback_data(query, limit)
        
        # Ensure all results have proper metadata
        for result in all_results:
            result.setdefault('search_keyword', business_type)
            result.setdefault('search_location', location)
            result.setdefault('full_query', query)
            result.setdefault('source', 'botasaurus')
        
        # Cache results
        if self.use_cache and all_results:
            self.cache_manager.cache_results(query, all_results, "business_leads")
        
        logger.info(f"BotasaurusProvider returning {len(all_results)} results")
        return all_results[:limit]
    
    @browser(
        headless=True,
        block_images=True,
        add_arguments=['--no-sandbox', '--disable-dev-shm-usage']
    )
    def _scrape_google_search(self, driver, dork_query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape Google search results using Botasaurus browser automation
        
        Args:
            driver: Botasaurus browser driver
            dork_query: Google dork query
            max_results: Maximum results to collect
            
        Returns:
            List of scraped business data
        """
        results = []
        
        try:
            # Configure anti-detection
            self.anti_detection.simulate_human_behavior(driver)
            
            # Navigate to Google
            google_url = f"https://www.google.com/search?q={quote(dork_query)}&num=20"
            driver.get(google_url)
            
            # Check for CAPTCHA
            if self._detect_captcha(driver):
                logger.warning("CAPTCHA detected, skipping this search")
                return results
            
            # Wait for results to load
            driver.sleep(2)
            
            # Extract search results
            search_results = driver.find_elements('css selector', '.g')
            
            for i, result_elem in enumerate(search_results[:max_results]):
                if i >= max_results:
                    break
                
                try:
                    # Extract basic info from search result
                    title_elem = result_elem.find_element('css selector', 'h3')
                    link_elem = result_elem.find_element('css selector', 'a')
                    snippet_elem = result_elem.find_element('css selector', '.VwiC3b')
                    
                    title = title_elem.text if title_elem else "Unknown Business"
                    url = link_elem.get_attribute('href') if link_elem else ""
                    snippet = snippet_elem.text if snippet_elem else ""
                    
                    # Extract contact info from snippet
                    emails = self.contact_extractor.extract_emails(snippet + " " + title)
                    phones = self.contact_extractor.extract_phones(snippet + " " + title)
                    
                    # Visit the actual website for more details
                    detailed_info = {}
                    if url and len(results) < max_results // 2:  # Visit only some pages for speed
                        detailed_info = self._scrape_website_details(driver, url)
                        self.anti_detection.random_delay(1, 2)
                    
                    # Combine information
                    business_data = {
                        'name': title,
                        'website': url,
                        'address': detailed_info.get('address', 'Address not found'),
                        'phone': phones[0] if phones else detailed_info.get('phone', ''),
                        'email': emails[0] if emails else detailed_info.get('email', ''),
                        'rating': detailed_info.get('rating', 0),
                        'reviews': detailed_info.get('reviews', 0),
                        'social_media': detailed_info.get('social_media', {}),
                        'description': snippet[:200] + "..." if len(snippet) > 200 else snippet,
                        'source': 'google_search',
                        'search_query': dork_query,
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    results.append(business_data)
                    
                except Exception as e:
                    logger.debug(f"Error extracting result {i}: {e}")
                    continue
            
            # Handle pagination if needed
            if len(results) < max_results:
                try:
                    next_button = driver.find_element('css selector', '#pnnext')
                    if next_button and next_button.is_displayed():
                        driver.execute_script("arguments[0].click();", next_button)
                        driver.sleep(3)
                        # Recursive call for next page (limited depth)
                        if hasattr(self, '_pagination_depth'):
                            self._pagination_depth += 1
                        else:
                            self._pagination_depth = 1
                        
                        if self._pagination_depth < 3:  # Max 3 pages
                            next_page_results = self._extract_current_page_results(driver, max_results - len(results))
                            results.extend(next_page_results)
                except Exception as e:
                    logger.debug(f"Pagination error: {e}")
            
        except Exception as e:
            logger.error(f"Error scraping Google search: {e}")
        
        return results
    
    def _scrape_website_details(self, driver, url: str) -> Dict[str, Any]:
        """
        Scrape detailed information from a business website
        
        Args:
            driver: Browser driver
            url: Website URL to scrape
            
        Returns:
            Dictionary with extracted business details
        """
        details = {}
        
        try:
            # Navigate to website
            driver.get(url)
            driver.sleep(2)
            
            # Get page text
            page_text = driver.get_page_source()
            
            # Extract contact information
            emails = self.contact_extractor.extract_emails(page_text)
            phones = self.contact_extractor.extract_phones(page_text)
            social_media = self.contact_extractor.extract_social_media(page_text, url)
            
            details.update({
                'email': emails[0] if emails else '',
                'phone': phones[0] if phones else '',
                'social_media': social_media,
            })
            
            # Try to find address
            address_patterns = [
                r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)[^,\n]*',
                r'(?:Address|Location)[\s:]+([^,\n]+)',
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    details['address'] = match.group(1 if match.groups() else 0).strip()
                    break
            
            # Look for ratings/reviews
            rating_pattern = r'(\d+\.?\d*)\s*(?:out of|\/)\s*(?:5|10)\s*(?:stars?|rating)'
            rating_match = re.search(rating_pattern, page_text, re.IGNORECASE)
            if rating_match:
                details['rating'] = float(rating_match.group(1))
            
            review_pattern = r'(\d+)\s*(?:reviews?|testimonials?)'
            review_match = re.search(review_pattern, page_text, re.IGNORECASE)
            if review_match:
                details['reviews'] = int(review_match.group(1))
            
        except Exception as e:
            logger.debug(f"Error scraping website details from {url}: {e}")
        
        return details
    
    def _scrape_with_dorks(self, dork_queries: List[str], max_results: int) -> List[Dict[str, Any]]:
        """
        Execute scraping with multiple dork queries
        
        Args:
            dork_queries: List of Google dork queries
            max_results: Maximum results to collect
            
        Returns:
            List of scraped business data
        """
        all_results = []
        results_per_dork = max(1, max_results // len(dork_queries)) if dork_queries else max_results
        
        for i, dork_query in enumerate(dork_queries):
            if len(all_results) >= max_results:
                break
            
            try:
                logger.info(f"Executing dork {i+1}/{len(dork_queries)}: {dork_query}")
                
                # Execute search with current dork
                dork_results = self._scrape_google_search(dork_query, results_per_dork)
                all_results.extend(dork_results)
                
                # Anti-detection delay between searches
                self.anti_detection.random_delay(2, 5)
                
            except Exception as e:
                logger.warning(f"Error with dork query '{dork_query}': {e}")
                continue
        
        logger.info(f"Collected {len(all_results)} results from {len(dork_queries)} dork queries")
        return all_results
    
    def _enhance_contact_info(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance existing results with additional contact information
        
        Args:
            results: List of business results to enhance
            
        Returns:
            Enhanced results with more contact information
        """
        enhanced_results = []
        
        for result in results:
            try:
                website = result.get('website', '')
                business_name = result.get('name', '')
                
                if website and business_name:
                    # Generate email hunting dorks for this specific business
                    domain = urlparse(website).netloc
                    email_dorks = self.dorks_engine.generate_email_hunting_dorks(business_name, domain)
                    
                    # Try to find more contact info
                    if not result.get('email') or not result.get('phone'):
                        for email_dork in email_dorks[:2]:  # Limit to 2 queries per business
                            try:
                                enhanced_info = self._scrape_google_search(email_dork, 3)
                                
                                # Extract additional contact info
                                for info in enhanced_info:
                                    if not result.get('email') and info.get('email'):
                                        result['email'] = info['email']
                                    if not result.get('phone') and info.get('phone'):
                                        result['phone'] = info['phone']
                                    if info.get('social_media'):
                                        result.setdefault('social_media', {}).update(info['social_media'])
                                
                            except Exception as e:
                                logger.debug(f"Error enhancing contact for {business_name}: {e}")
                                break
                
                enhanced_results.append(result)
                
            except Exception as e:
                logger.debug(f"Error enhancing result: {e}")
                enhanced_results.append(result)
        
        return enhanced_results
    
    def _scrape_social_media(self, business_type: str, location: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Scrape social media platforms for business information
        
        Args:
            business_type: Type of business
            location: Business location
            max_results: Maximum results
            
        Returns:
            List of businesses found on social media
        """
        social_results = []
        
        social_dorks = self.dorks_engine.generate_social_media_dorks(business_type, location)
        
        for dork in social_dorks[:5]:  # Limit social media searches
            try:
                results = self._scrape_google_search(dork, max_results // 5)
                social_results.extend(results)
                
                if len(social_results) >= max_results:
                    break
                    
                self.anti_detection.random_delay(1, 3)
                
            except Exception as e:
                logger.debug(f"Error scraping social media with dork '{dork}': {e}")
                continue
        
        return social_results
    
    def _detect_captcha(self, driver) -> bool:
        """
        Detect if Google is showing a CAPTCHA
        
        Args:
            driver: Browser driver
            
        Returns:
            True if CAPTCHA detected
        """
        try:
            # Look for common CAPTCHA indicators
            captcha_indicators = [
                'recaptcha',
                'captcha',
                'unusual traffic',
                'verify you are human',
                'security check',
                'robot'
            ]
            
            page_text = driver.get_page_source().lower()
            
            for indicator in captcha_indicators:
                if indicator in page_text:
                    return True
            
            # Check for CAPTCHA elements
            captcha_elements = [
                '#captcha',
                '.captcha',
                '[id*="captcha"]',
                '[class*="captcha"]',
                '#recaptcha',
                '.g-recaptcha'
            ]
            
            for selector in captcha_elements:
                try:
                    if driver.find_element('css selector', selector):
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"Error detecting CAPTCHA: {e}")
            return False
    
    def _deduplicate_results(self, results: List[Dict[str, Any]], seen_businesses: Set[str]) -> List[Dict[str, Any]]:
        """
        Remove duplicate businesses from results
        
        Args:
            results: List of business results
            seen_businesses: Set of already seen business identifiers
            
        Returns:
            Deduplicated results
        """
        unique_results = []
        
        for result in results:
            # Create business identifier
            name = result.get('name', '').lower().strip()
            address = result.get('address', '').lower().strip()
            
            # Clean business name for better matching
            name_clean = re.sub(r'[^\w\s]', '', name).strip()
            
            # Create multiple identifiers for better deduplication
            identifiers = [
                name,
                name_clean,
                f"{name}_{address[:20]}" if address else name,
            ]
            
            # Check if any identifier has been seen
            is_duplicate = any(identifier in seen_businesses for identifier in identifiers if identifier)
            
            if not is_duplicate and name:
                # Add all identifiers to seen set
                for identifier in identifiers:
                    if identifier:
                        seen_businesses.add(identifier)
                
                unique_results.append(result)
        
        logger.debug(f"Deduplicated {len(results)} -> {len(unique_results)} results")
        return unique_results
    
    def _parse_query(self, query: str) -> tuple:
        """
        Parse search query to extract business type and location
        
        Args:
            query: Search query (e.g., "dentists in Miami")
            
        Returns:
            Tuple of (business_type, location)
        """
        query = query.strip().lower()
        
        # Look for " in " separator
        if ' in ' in query:
            parts = query.split(' in ', 1)
            return parts[0].strip(), parts[1].strip()
        
        # Look for " near " separator
        elif ' near ' in query:
            parts = query.split(' near ', 1)
            return parts[0].strip(), parts[1].strip()
        
        # Try to infer from query structure
        elif ',' in query:
            parts = query.split(',', 1)
            return parts[0].strip(), parts[1].strip()
        
        # Default: assume it's business type only
        else:
            return query, 'united states'
    
    def _get_fallback_data(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Generate fallback sample data when scraping fails
        
        Args:
            query: Original query
            limit: Number of results needed
            
        Returns:
            List of sample business data
        """
        business_type, location = self._parse_query(query)
        
        sample_data = []
        for i in range(min(limit, 10)):
            sample_data.append({
                'name': f"{business_type.title()} Pro {i+1}",
                'address': f"{100+i*50} Business Ave, {location.title()}",
                'phone': f"(555) {200+i:03d}-{3000+i:04d}",
                'email': f"contact{i+1}@{business_type.lower().replace(' ', '')}.com",
                'website': f"https://www.{business_type.lower().replace(' ', '')}{i+1}.com",
                'rating': round(3.5 + random.random() * 1.5, 1),
                'reviews': random.randint(10, 200),
                'social_media': {
                    'facebook': f"https://facebook.com/{business_type.replace(' ', '')}{i+1}",
                },
                'description': f"Professional {business_type} services in {location}",
                'source': 'fallback_data',
                'search_keyword': business_type,
                'search_location': location,
                'full_query': query
            })
        
        logger.info(f"Generated {len(sample_data)} fallback results for query: {query}")
        return sample_data
    
    def _extract_current_page_results(self, driver, max_results: int) -> List[Dict[str, Any]]:
        """
        Extract results from the current Google search page
        
        Args:
            driver: Browser driver
            max_results: Maximum results to extract
            
        Returns:
            List of extracted results
        """
        results = []
        
        try:
            search_results = driver.find_elements('css selector', '.g')
            
            for i, result_elem in enumerate(search_results[:max_results]):
                try:
                    title_elem = result_elem.find_element('css selector', 'h3')
                    link_elem = result_elem.find_element('css selector', 'a')
                    snippet_elem = result_elem.find_element('css selector', '.VwiC3b')
                    
                    title = title_elem.text if title_elem else "Unknown Business"
                    url = link_elem.get_attribute('href') if link_elem else ""
                    snippet = snippet_elem.text if snippet_elem else ""
                    
                    # Quick contact extraction
                    emails = self.contact_extractor.extract_emails(snippet + " " + title)
                    phones = self.contact_extractor.extract_phones(snippet + " " + title)
                    
                    business_data = {
                        'name': title,
                        'website': url,
                        'address': 'Address available on website',
                        'phone': phones[0] if phones else '',
                        'email': emails[0] if emails else '',
                        'rating': 0,
                        'reviews': 0,
                        'description': snippet[:200],
                        'source': 'google_pagination',
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    results.append(business_data)
                    
                except Exception as e:
                    logger.debug(f"Error extracting paginated result {i}: {e}")
                    continue
        
        except Exception as e:
            logger.debug(f"Error extracting current page results: {e}")
        
        return results