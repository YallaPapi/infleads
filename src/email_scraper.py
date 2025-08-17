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
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class WebsiteEmailScraper:
    """Scrapes emails and contact person names directly from business websites"""
    
    # Common email patterns
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    # Name patterns for extracting first names from websites
    NAME_PATTERNS = [
        # CEO/Owner patterns with names after title
        re.compile(r'(?:CEO|Owner|President|Founder|Director|Manager|Partner)[\s:,-]+([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
        # Name followed by title
        re.compile(r'([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)*?)[\s,-]+(?:CEO|Owner|President|Founder|Director|Manager|Partner)', re.IGNORECASE),
        # Contact person patterns
        re.compile(r'Contact[\s:,-]+([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
        # Meet patterns
        re.compile(r'Meet[\s:,-]*(?:our\s+)?([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
        # About patterns
        re.compile(r'(?:I\'m|My name is|Hi,?\s*I\'m|Hello,?\s*I\'m)[\s:,-]*([A-Z][a-z]{2,})', re.IGNORECASE),
        # Team member patterns in headings
        re.compile(r'<h[1-6][^>]*>\s*([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)?)\s*</h[1-6]>', re.IGNORECASE),
        # Staff directory patterns
        re.compile(r'(?:Dr\.|Mr\.|Ms\.|Mrs\.)\s*([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
        # Email signature patterns
        re.compile(r'Best regards,?\s*([A-Z][a-z]{2,})', re.IGNORECASE),
        re.compile(r'Sincerely,?\s*([A-Z][a-z]{2,})', re.IGNORECASE),
        # Team page patterns
        re.compile(r'(?:Team member|Staff|Employee)[\s:,-]*([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
        # Bio patterns
        re.compile(r'([A-Z][a-z]{2,})\s+has\s+(?:over\s+)?\d+\s+years?\s+of\s+experience', re.IGNORECASE),
        # Professional patterns
        re.compile(r'([A-Z][a-z]{2,})\s+(?:is|serves as|works as)\s+(?:our\s+)?(?:CEO|Owner|President|Founder|Director|Manager)', re.IGNORECASE)
    ]
    
    # Common first names to validate extractions
    COMMON_FIRST_NAMES = {
        'james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 'charles',
        'joseph', 'thomas', 'christopher', 'daniel', 'paul', 'mark', 'donald', 'steven',
        'andrew', 'joshua', 'kenneth', 'kevin', 'brian', 'george', 'edward', 'ronald',
        'timothy', 'jason', 'jeffrey', 'ryan', 'jacob', 'gary', 'nicholas', 'eric',
        'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan',
        'jessica', 'sarah', 'karen', 'nancy', 'lisa', 'betty', 'helen', 'sandra',
        'donna', 'carol', 'ruth', 'sharon', 'michelle', 'laura', 'sarah', 'kimberly',
        'deborah', 'dorothy', 'amy', 'angela', 'ashley', 'brenda', 'emma', 'olivia',
        'cynthia', 'marie', 'janet', 'catherine', 'frances', 'christine', 'samantha'
    }
    
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
        '/get-in-touch',
        '/meet-the-team',
        '/our-team',
        '/leadership',
        '/management'
    ]
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_names_from_content(self, content: str) -> List[str]:
        """Extract potential first names from website content"""
        found_names = set()
        
        try:
            # Parse HTML and extract text for better matching
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            
            # Also check HTML structure for headings and specific elements
            html_content = str(soup)
            
            # Search in both text and HTML content
            for content_to_search in [text_content, html_content]:
                for pattern in self.NAME_PATTERNS:
                    matches = pattern.findall(content_to_search)
                    for match in matches:
                        if isinstance(match, tuple):
                            name = match[0] if match[0] else match[1] if len(match) > 1 else ''
                        else:
                            name = match
                        
                        # Clean and extract first name
                        if name:
                            # Remove extra whitespace and clean
                            name = ' '.join(name.split())
                            first_name = name.split()[0].lower().strip()
                            
                            # Filter out business-related words and validate it's a real name
                            business_words = {'company', 'corp', 'corporation', 'inc', 'llc', 'ltd', 
                                            'group', 'associates', 'partners', 'firm', 'agency', 
                                            'services', 'solutions', 'consulting', 'the', 'and', 
                                            'our', 'meet', 'about', 'contact', 'team', 'staff'}
                            
                            if (len(first_name) >= 2 and 
                                first_name.isalpha() and 
                                first_name not in business_words and
                                not any(word in name.lower() for word in ['company', 'corp', 'inc', 'llc']) and
                                (first_name in self.COMMON_FIRST_NAMES or len(first_name) >= 3)):
                                found_names.add(first_name.capitalize())
                                
                                # Stop after finding 3 names to avoid over-processing
                                if len(found_names) >= 3:
                                    break
                    
                    if len(found_names) >= 3:
                        break
                        
        except Exception as e:
            logger.debug(f"Error parsing HTML content: {e}")
            # Fallback to simple text search
            for pattern in self.NAME_PATTERNS:
                matches = pattern.findall(content)
                for match in matches:
                    if isinstance(match, tuple):
                        name = match[0] if match[0] else match[1] if len(match) > 1 else ''
                    else:
                        name = match
                    
                    if name:
                        first_name = name.split()[0].lower() if name else ''
                        if (len(first_name) >= 2 and 
                            first_name.isalpha() and 
                            (first_name in self.COMMON_FIRST_NAMES or len(first_name) >= 3)):
                            found_names.add(first_name.capitalize())
        
        return list(found_names)[:3]  # Return top 3 names found
    
    def extract_contact_info_from_website(self, website_url: str, advanced_scraping: bool = False) -> dict:
        """Extract both email and contact person names from website"""
        result = {
            'email': None,
            'first_names': [],
            'contact_person': None,
            'job_title': None
        }
        
        if not website_url or website_url == 'NA':
            return result
        
        emails_found = set()
        all_content = ""
        
        # Try different contact pages
        for path in self.CONTACT_PATHS:
            try:
                url = website_url.rstrip('/') + path
                response = self.session.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    content = response.text
                    all_content += content + " "
                    
                    # Extract emails
                    emails = self.EMAIL_PATTERN.findall(content)
                    for email in emails:
                        email = email.lower()
                        if email not in self.SKIP_EMAILS and '@' in email:
                            emails_found.add(email)
                            
                    # If we found emails, we can stop early unless doing advanced scraping
                    if emails_found and not advanced_scraping:
                        break
                        
            except Exception as e:
                logger.debug(f"Error scraping {url}: {e}")
                continue
        
        # Set the best email found
        if emails_found:
            domain = website_url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
            for email in emails_found:
                if domain in email:
                    result['email'] = email
                    break
            if not result['email']:
                result['email'] = list(emails_found)[0]
        
        # Advanced scraping: extract names and contact person info
        if advanced_scraping and all_content:
            result['first_names'] = self.extract_names_from_content(all_content)
            
            # Try to find a primary contact person
            if result['first_names']:
                result['contact_person'] = result['first_names'][0]
                
                # Try to find job title for the first name found
                first_name = result['first_names'][0]
                title_patterns = [
                    re.compile(rf'{first_name}[^,]*,\s*([^,\n]+)', re.IGNORECASE),
                    re.compile(rf'{first_name}[^-]*-\s*([^,\n]+)', re.IGNORECASE),
                    re.compile(rf'({first_name}[^,]*(?:CEO|Owner|President|Founder|Director|Manager))', re.IGNORECASE)
                ]
                
                for pattern in title_patterns:
                    match = pattern.search(all_content)
                    if match:
                        result['job_title'] = match.group(1).strip()[:50]  # Limit length
                        break
        
        return result

    def extract_email_from_website(self, website_url: str) -> Optional[str]:
        """Legacy method for backward compatibility"""
        result = self.extract_contact_info_from_website(website_url, advanced_scraping=False)
        return result['email']
    
    def scrape_contacts_bulk(self, leads: List[dict], max_workers: int = 10, advanced_scraping: bool = False) -> List[dict]:
        """
        Scrape emails and contact info for multiple leads in parallel
        
        Args:
            leads: List of lead dictionaries with 'Website' field
            max_workers: Number of parallel threads
            advanced_scraping: If True, also extract names and contact person info
            
        Returns:
            Updated leads with scraped emails and contact info
        """
        scrape_type = "contact info" if advanced_scraping else "email"
        logger.info(f"Starting {scrape_type} scraping for {len(leads)} leads...")
        
        def process_lead(lead):
            """Process a single lead"""
            # Skip if email already exists and not doing advanced scraping
            if not advanced_scraping and lead.get('Email') and lead['Email'] != 'NA':
                return lead
                
            website = lead.get('Website', '')
            if website and website != 'NA':
                contact_info = self.extract_contact_info_from_website(website, advanced_scraping)
                
                # Update email if found
                if contact_info['email']:
                    lead['Email'] = contact_info['email']
                    lead['email_source'] = 'website_scrape'
                    logger.debug(f"Found email {contact_info['email']} for {lead.get('Name', 'Unknown')}")
                
                # Update contact info if advanced scraping
                if advanced_scraping:
                    if contact_info['contact_person']:
                        lead['ContactPerson'] = contact_info['contact_person']
                        lead['FirstName'] = contact_info['contact_person']
                        logger.debug(f"Found contact person {contact_info['contact_person']} for {lead.get('Name', 'Unknown')}")
                    
                    if contact_info['job_title']:
                        lead['JobTitle'] = contact_info['job_title']
                    
                    if contact_info['first_names']:
                        lead['AllNames'] = ', '.join(contact_info['first_names'])
            
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
    
    def scrape_emails_bulk(self, leads: List[dict], max_workers: int = 10) -> List[dict]:
        """Legacy method for backward compatibility"""
        return self.scrape_contacts_bulk(leads, max_workers, advanced_scraping=False)


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