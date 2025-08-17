"""
Simple email scraper that extracts emails from websites
Much cheaper than using Apify's email enrichment!
"""

import re
import requests
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os

logger = logging.getLogger(__name__)

class WebsiteEmailScraper:
    """Scrapes emails directly from business websites"""
    
    # Common email patterns
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    # Skip these common non-business emails
    SKIP_EMAILS = {
        'example@email.com',
        'your@email.com',
        'name@domain.com',
        'info@domain.com',  # Too generic, keep only if nothing else
        'support@domain.com',
        'hello@domain.com'
    }
    
    # Common contact page paths to check
    CONTACT_PATHS = [
        '',  # Homepage
        '/contact',
        '/contact-us',
        '/contactus',
        '/about',
        '/about-us',
        '/team',
        '/staff',
        '/location',
        '/locations',
        '/get-in-touch'
    ]
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_email_from_website(self, website_url: str) -> Optional[str]:
        """
        Extract email from a website by checking multiple pages
        
        Args:
            website_url: The website URL to scrape
            
        Returns:
            Email address or None if not found
        """
        if not website_url or website_url == 'NA':
            return None
            
        # Ensure URL has protocol
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
            
        emails_found = set()
        
        # Try different contact pages
        for path in self.CONTACT_PATHS[:3]:  # Limit to avoid too many requests
            try:
                url = urljoin(website_url, path)
                response = self.session.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    # Find all emails on the page
                    page_emails = self.EMAIL_PATTERN.findall(response.text)
                    
                    # Filter out invalid/generic emails
                    for email in page_emails:
                        email_lower = email.lower()
                        if (email_lower not in self.SKIP_EMAILS and 
                            not email_lower.endswith('.png') and
                            not email_lower.endswith('.jpg') and
                            not email_lower.startswith('wix')):
                            emails_found.add(email)
                            
            except Exception as e:
                logger.debug(f"Error checking {url}: {e}")
                continue
        
        # Return the best email found
        if emails_found:
            # Prefer emails with the business domain
            domain = urlparse(website_url).netloc.replace('www.', '')
            for email in emails_found:
                if domain in email:
                    return email
            # Otherwise return first email found
            return list(emails_found)[0]
            
        return None
    
    def scrape_emails_bulk(self, leads: List[dict], max_workers: int = 10) -> List[dict]:
        """
        Scrape emails for multiple leads in parallel
        
        Args:
            leads: List of lead dictionaries with 'Website' field
            max_workers: Number of parallel threads
            
        Returns:
            Updated leads with scraped emails
        """
        logger.info(f"Starting email scraping for {len(leads)} leads...")
        
        def process_lead(lead):
            """Process a single lead"""
            # Skip if email already exists
            if lead.get('Email') and lead['Email'] != 'NA':
                return lead
                
            website = lead.get('Website', '')
            if website and website != 'NA':
                email = self.extract_email_from_website(website)
                if email:
                    lead['Email'] = email
                    lead['email_source'] = 'website_scrape'
                    logger.debug(f"Found email {email} for {lead.get('Name', 'Unknown')}")
            
            return lead
        
        # Process leads in parallel
        updated_leads = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_lead, lead): lead for lead in leads}
            
            for future in as_completed(futures):
                try:
                    updated_lead = future.result()
                    updated_leads.append(updated_lead)
                except Exception as e:
                    logger.error(f"Error processing lead: {e}")
                    updated_leads.append(futures[future])  # Add original if failed
        
        # Count results
        emails_found = sum(1 for lead in updated_leads 
                          if lead.get('Email') and lead['Email'] != 'NA')
        logger.info(f"Email scraping complete: found {emails_found}/{len(leads)} emails")
        
        return updated_leads


class HunterIOScraper:
    """
    Alternative using Hunter.io API (if you want to pay for better quality)
    Pricing: $49/month for 1,000 verifications
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('HUNTER_API_KEY')
        self.base_url = 'https://api.hunter.io/v2'
    
    def find_email(self, domain: str, first_name: str = None, last_name: str = None) -> Optional[str]:
        """Find email using Hunter.io domain search"""
        if not self.api_key:
            return None
            
        try:
            # Domain search to find email pattern
            response = requests.get(
                f'{self.base_url}/domain-search',
                params={
                    'domain': domain,
                    'api_key': self.api_key
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                emails = data.get('data', {}).get('emails', [])
                if emails:
                    # Return first email found
                    return emails[0].get('value')
                    
        except Exception as e:
            logger.error(f"Hunter.io error: {e}")
            
        return None