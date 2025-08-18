"""
Lead Enrichment Module
Adds social media, company size, technology stack, and other enrichment data
"""

import requests
import re
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote
import json

logger = logging.getLogger(__name__)

class LeadEnricher:
    """
    Enriches leads with additional data points
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = 5
    
    def enrich_lead(self, lead: Dict) -> Dict:
        """
        Enrich a lead with all available data
        """
        enriched = lead.copy()
        
        # Get website domain
        website = lead.get('website') or lead.get('Website')
        if website and website != 'NA':
            domain = self._extract_domain(website)
            
            # Social media discovery
            social_links = self.find_social_media(domain, lead.get('name', ''))
            enriched['social_media'] = social_links
            
            # Company size estimation
            company_size = self.estimate_company_size(website, lead.get('name', ''))
            enriched['company_size'] = company_size
            
            # Technology stack detection
            tech_stack = self.detect_technology_stack(website)
            enriched['technology_stack'] = tech_stack
            
            # Business type classification
            business_type = self.classify_business_type(lead)
            enriched['business_type'] = business_type
        
        # Phone number type detection
        phone_type = self.detect_phone_type(lead.get('phone', ''))
        enriched['phone_type'] = phone_type
        
        return enriched
    
    def find_social_media(self, domain: str, business_name: str) -> Dict[str, str]:
        """
        Find social media profiles for a business
        """
        social_links = {
            'linkedin': None,
            'facebook': None,
            'twitter': None,
            'instagram': None,
            'youtube': None
        }
        
        try:
            # Method 1: Check website for social links
            website_social = self._extract_social_from_website(f"https://{domain}")
            social_links.update(website_social)
            
            # Method 2: Search social platforms directly
            if not social_links['linkedin']:
                social_links['linkedin'] = self._search_linkedin(business_name)
            
            if not social_links['facebook']:
                social_links['facebook'] = self._search_facebook(business_name)
            
            if not social_links['twitter']:
                social_links['twitter'] = self._search_twitter(business_name)
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"Network error finding social media for {business_name}: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error finding social media for {business_name}: {e}", exc_info=True)
        
        return social_links
    
    def _extract_social_from_website(self, website: str) -> Dict[str, str]:
        """
        Extract social media links from a website
        """
        social_patterns = {
            'linkedin': r'linkedin\.com/company/([^/\s"\']+)',
            'facebook': r'facebook\.com/([^/\s"\']+)',
            'twitter': r'twitter\.com/([^/\s"\']+)',
            'instagram': r'instagram\.com/([^/\s"\']+)',
            'youtube': r'youtube\.com/(?:c/|channel/|user/)([^/\s"\']+)'
        }
        
        social_links = {}
        
        try:
            response = self.session.get(website, timeout=self.timeout)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            content = response.text
            
            for platform, pattern in social_patterns.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    username = match.group(1)
                    if platform == 'linkedin':
                        social_links[platform] = f"https://linkedin.com/company/{username}"
                    elif platform == 'facebook':
                        social_links[platform] = f"https://facebook.com/{username}"
                    elif platform == 'twitter':
                        social_links[platform] = f"https://twitter.com/{username}"
                    elif platform == 'instagram':
                        social_links[platform] = f"https://instagram.com/{username}"
                    elif platform == 'youtube':
                        social_links[platform] = f"https://youtube.com/c/{username}"
        
        except requests.exceptions.HTTPError as e:
            logger.debug(f"HTTP error extracting social from {website}: {e}")
        except requests.exceptions.RequestException as e:
            logger.debug(f"Network error extracting social from {website}: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error extracting social from {website}: {e}", exc_info=True)
        
        return social_links
    
    def _search_linkedin(self, business_name: str) -> Optional[str]:
        """
        Search for LinkedIn company page
        """
        try:
            # Use Google to search for LinkedIn page
            search_query = f"site:linkedin.com/company {business_name}"
            search_url = f"https://www.google.com/search?q={quote(search_query)}"
            
            response = self.session.get(search_url, timeout=self.timeout)
            if response.status_code == 200:
                # Extract first LinkedIn company URL from results
                match = re.search(r'linkedin\.com/company/[^/\s&"]+', response.text)
                if match:
                    return f"https://{match.group(0)}"
        except:
            pass
        return None
    
    def _search_facebook(self, business_name: str) -> Optional[str]:
        """
        Search for Facebook page
        """
        try:
            # Facebook search is more restricted, use Google
            search_query = f"site:facebook.com {business_name}"
            search_url = f"https://www.google.com/search?q={quote(search_query)}"
            
            response = self.session.get(search_url, timeout=self.timeout)
            if response.status_code == 200:
                match = re.search(r'facebook\.com/[^/\s&"]+', response.text)
                if match:
                    return f"https://{match.group(0)}"
        except:
            pass
        return None
    
    def _search_twitter(self, business_name: str) -> Optional[str]:
        """
        Search for Twitter/X profile
        """
        try:
            search_query = f"site:twitter.com {business_name}"
            search_url = f"https://www.google.com/search?q={quote(search_query)}"
            
            response = self.session.get(search_url, timeout=self.timeout)
            if response.status_code == 200:
                match = re.search(r'twitter\.com/[^/\s&"]+', response.text)
                if match:
                    return f"https://{match.group(0)}"
        except:
            pass
        return None
    
    def estimate_company_size(self, website: str, business_name: str) -> Dict:
        """
        Estimate company size based on various signals
        """
        size_data = {
            'estimated_employees': 'Unknown',
            'company_type': 'Unknown',
            'confidence': 'low'
        }
        
        try:
            response = self.session.get(website, timeout=self.timeout)
            if response.status_code == 200:
                content = response.text.lower()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for employee count mentions
                employee_patterns = [
                    r'(\d+)\+?\s*employees',
                    r'team of\s*(\d+)',
                    r'(\d+)\s*people',
                    r'(\d+)\s*staff'
                ]
                
                for pattern in employee_patterns:
                    match = re.search(pattern, content)
                    if match:
                        count = int(match.group(1))
                        size_data['estimated_employees'] = self._categorize_company_size(count)
                        size_data['confidence'] = 'high'
                        break
                
                # Check for company type indicators
                if 'enterprise' in content or 'fortune 500' in content:
                    size_data['company_type'] = 'Enterprise'
                    if size_data['estimated_employees'] == 'Unknown':
                        size_data['estimated_employees'] = '500+'
                        size_data['confidence'] = 'medium'
                elif 'startup' in content or 'founded in 20' in content:
                    size_data['company_type'] = 'Startup'
                    if size_data['estimated_employees'] == 'Unknown':
                        size_data['estimated_employees'] = '1-50'
                        size_data['confidence'] = 'medium'
                elif 'family owned' in content or 'family business' in content:
                    size_data['company_type'] = 'Family Business'
                    if size_data['estimated_employees'] == 'Unknown':
                        size_data['estimated_employees'] = '1-20'
                        size_data['confidence'] = 'medium'
                
                # Check for office locations (multiple = larger company)
                location_indicators = ['locations', 'offices', 'branches']
                for indicator in location_indicators:
                    if indicator in content:
                        match = re.search(rf'(\d+)\s*{indicator}', content)
                        if match and int(match.group(1)) > 3:
                            size_data['company_type'] = 'Multi-location Business'
                            if size_data['estimated_employees'] == 'Unknown':
                                size_data['estimated_employees'] = '50-500'
                                size_data['confidence'] = 'medium'
                
        except Exception as e:
            logger.debug(f"Error estimating company size: {e}")
        
        return size_data
    
    def _categorize_company_size(self, employee_count: int) -> str:
        """
        Categorize company based on employee count
        """
        if employee_count <= 10:
            return '1-10'
        elif employee_count <= 50:
            return '11-50'
        elif employee_count <= 200:
            return '51-200'
        elif employee_count <= 500:
            return '201-500'
        elif employee_count <= 1000:
            return '501-1000'
        else:
            return '1000+'
    
    def detect_technology_stack(self, website: str) -> Dict[str, List[str]]:
        """
        Detect technologies used by the website
        """
        tech_stack = {
            'cms': [],
            'analytics': [],
            'frameworks': [],
            'ecommerce': [],
            'marketing': [],
            'payment': [],
            'hosting': []
        }
        
        try:
            response = self.session.get(website, timeout=self.timeout)
            if response.status_code == 200:
                content = response.text
                headers = response.headers
                
                # CMS Detection
                if 'wordpress' in content.lower() or 'wp-content' in content:
                    tech_stack['cms'].append('WordPress')
                if 'shopify' in content.lower() or 'cdn.shopify' in content:
                    tech_stack['cms'].append('Shopify')
                    tech_stack['ecommerce'].append('Shopify')
                if 'wix' in content.lower() or 'wix.com' in content:
                    tech_stack['cms'].append('Wix')
                if 'squarespace' in content.lower():
                    tech_stack['cms'].append('Squarespace')
                if 'joomla' in content.lower():
                    tech_stack['cms'].append('Joomla')
                if 'drupal' in content.lower():
                    tech_stack['cms'].append('Drupal')
                
                # Analytics Detection
                if 'google-analytics' in content or 'gtag' in content or 'ga.js' in content:
                    tech_stack['analytics'].append('Google Analytics')
                if 'facebook.com/tr' in content:
                    tech_stack['analytics'].append('Facebook Pixel')
                if 'hotjar' in content:
                    tech_stack['analytics'].append('Hotjar')
                if 'segment' in content:
                    tech_stack['analytics'].append('Segment')
                
                # Framework Detection
                if 'react' in content.lower() or 'reactjs' in content:
                    tech_stack['frameworks'].append('React')
                if 'angular' in content.lower():
                    tech_stack['frameworks'].append('Angular')
                if 'vue.js' in content or 'vuejs' in content:
                    tech_stack['frameworks'].append('Vue.js')
                if 'bootstrap' in content.lower():
                    tech_stack['frameworks'].append('Bootstrap')
                if 'jquery' in content.lower():
                    tech_stack['frameworks'].append('jQuery')
                
                # E-commerce Detection
                if 'woocommerce' in content.lower():
                    tech_stack['ecommerce'].append('WooCommerce')
                if 'magento' in content.lower():
                    tech_stack['ecommerce'].append('Magento')
                if 'bigcommerce' in content.lower():
                    tech_stack['ecommerce'].append('BigCommerce')
                
                # Marketing Tools
                if 'mailchimp' in content.lower():
                    tech_stack['marketing'].append('Mailchimp')
                if 'hubspot' in content.lower():
                    tech_stack['marketing'].append('HubSpot')
                if 'marketo' in content.lower():
                    tech_stack['marketing'].append('Marketo')
                if 'pardot' in content.lower():
                    tech_stack['marketing'].append('Pardot')
                if 'activecampaign' in content.lower():
                    tech_stack['marketing'].append('ActiveCampaign')
                
                # Payment Processing
                if 'stripe' in content.lower():
                    tech_stack['payment'].append('Stripe')
                if 'paypal' in content.lower():
                    tech_stack['payment'].append('PayPal')
                if 'square' in content.lower():
                    tech_stack['payment'].append('Square')
                
                # Hosting Detection (from headers)
                server = headers.get('Server', '').lower()
                x_powered_by = headers.get('X-Powered-By', '').lower()
                
                if 'cloudflare' in server or 'cloudflare' in str(headers):
                    tech_stack['hosting'].append('Cloudflare')
                if 'amazon' in server or 'aws' in server:
                    tech_stack['hosting'].append('AWS')
                if 'nginx' in server:
                    tech_stack['hosting'].append('Nginx')
                if 'apache' in server:
                    tech_stack['hosting'].append('Apache')
                
        except Exception as e:
            logger.debug(f"Error detecting technology stack: {e}")
        
        # Remove empty categories
        tech_stack = {k: v for k, v in tech_stack.items() if v}
        
        return tech_stack
    
    def classify_business_type(self, lead: Dict) -> str:
        """
        Classify the type of business based on available data
        """
        categories = lead.get('categories', []) or lead.get('types', [])
        name = (lead.get('name') or lead.get('Name', '')).lower()
        
        # B2B indicators
        b2b_keywords = ['consulting', 'agency', 'software', 'solutions', 'services', 
                       'partners', 'associates', 'group', 'corporation', 'inc', 'llc', 
                       'enterprise', 'systems', 'technologies']
        
        # B2C indicators
        b2c_keywords = ['restaurant', 'cafe', 'shop', 'store', 'salon', 'spa', 
                       'fitness', 'gym', 'clinic', 'dental', 'medical', 'retail',
                       'boutique', 'bar', 'pizza', 'coffee']
        
        # Check categories first
        categories_str = ' '.join(categories).lower()
        
        b2b_score = sum(1 for keyword in b2b_keywords if keyword in name or keyword in categories_str)
        b2c_score = sum(1 for keyword in b2c_keywords if keyword in name or keyword in categories_str)
        
        if b2b_score > b2c_score:
            return 'B2B'
        elif b2c_score > b2b_score:
            return 'B2C'
        else:
            return 'B2B/B2C'
    
    def detect_phone_type(self, phone: str) -> str:
        """
        Detect if phone number is mobile, landline, toll-free, etc.
        """
        if not phone or phone == 'NA':
            return 'Unknown'
        
        # Clean phone number
        digits = re.sub(r'\D', '', phone)
        
        # US toll-free prefixes
        toll_free = ['800', '888', '877', '866', '855', '844', '833']
        
        if len(digits) >= 10:
            area_code = digits[-10:-7] if len(digits) > 10 else digits[:3]
            
            if area_code in toll_free:
                return 'Toll-Free'
            
            # This would require a more sophisticated database
            # For now, just return "Business"
            return 'Business'
        
        return 'Unknown'
    
    def _extract_domain(self, website: str) -> str:
        """
        Extract domain from website URL
        """
        if not website.startswith('http'):
            website = f'http://{website}'
        
        parsed = urlparse(website)
        domain = parsed.netloc or parsed.path
        
        # Remove www.
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain