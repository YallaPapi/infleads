#!/usr/bin/env python3
"""
Google Dorks Engine - Advanced search query generation for business discovery
"""

import logging
import random
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DorksEngine:
    """
    Advanced Google dorks engine for business lead generation
    Generates sophisticated search queries to find businesses with contact info
    """
    
    def __init__(self):
        self.business_type_mapping = {
            'dentist': ['dental', 'dentistry', 'orthodontics', 'oral surgeon', 'dental clinic'],
            'lawyer': ['attorney', 'legal', 'law firm', 'legal services', 'counsel'],
            'doctor': ['physician', 'medical', 'clinic', 'healthcare', 'medical center'],
            'restaurant': ['dining', 'food', 'eatery', 'bistro', 'cafe'],
            'plumber': ['plumbing', 'pipe repair', 'drain cleaning', 'water heater'],
            'electrician': ['electrical', 'wiring', 'electrical contractor', 'electric repair'],
            'accountant': ['accounting', 'tax preparation', 'bookkeeping', 'financial services'],
            'realtor': ['real estate', 'property', 'realtor', 'real estate agent'],
            'contractor': ['construction', 'building', 'home improvement', 'general contractor'],
            'mechanic': ['auto repair', 'car service', 'automotive', 'vehicle repair']
        }
        
        self.contact_dorks = [
            'intitle:"contact us"',
            'intitle:"about us"',
            'intitle:"contact"',
            'intext:"phone:"',
            'intext:"email:"',
            'intext:"call us"',
            'intext:"contact information"',
            'filetype:pdf "contact"',
            'inurl:contact',
            'inurl:about'
        ]
        
        self.email_dorks = [
            'intext:"@" "phone"',
            'intext:"email:" OR "e-mail:"',
            'intext:"mailto:"',
            'intext:"contact@"',
            'intext:"info@"',
            'intext:"sales@"',
            'filetype:pdf "@"'
        ]
        
        self.phone_dorks = [
            'intext:"phone:" OR "tel:" OR "call:"',
            'intext:"(" ")" "-" phone',
            'intext:"555-" OR "phone:"',
            'intext:"call us" phone',
            'intext:"telephone:"',
            'intext:"mobile:"'
        ]
        
        self.business_page_dorks = [
            'site:facebook.com/pages',
            'site:linkedin.com/company',
            'site:yelp.com',
            'site:yellowpages.com',
            'site:google.com/maps',
            'site:foursquare.com',
            'site:bbb.org',
            'inurl:reviews',
            'inurl:directory'
        ]
    
    def generate_business_dorks(self, business_type: str, location: str, 
                               include_contact: bool = True) -> List[str]:
        """
        Generate sophisticated dorks for finding businesses
        
        Args:
            business_type: Type of business (e.g., "dentist", "lawyer")
            location: Location to search (e.g., "Miami", "New York")
            include_contact: Whether to include contact info dorks
            
        Returns:
            List of Google dork queries
        """
        dorks = []
        
        # Normalize business type
        business_variations = self._get_business_variations(business_type)
        
        # Basic business finding dorks
        for variation in business_variations[:3]:  # Use top 3 variations
            # Standard location-based searches
            dorks.extend([
                f'"{variation}" "{location}"',
                f'"{variation}" near "{location}"',
                f'"{variation}" in "{location}"',
                f'intitle:"{variation}" "{location}"',
                f'allintitle:"{variation}" "{location}"'
            ])
            
            # Directory-based searches
            for site_dork in self.business_page_dorks[:4]:  # Top 4 sites
                dorks.append(f'{site_dork} "{variation}" "{location}"')
        
        # Contact information focused dorks
        if include_contact:
            primary_business = business_variations[0] if business_variations else business_type
            
            # Email-focused searches
            for email_dork in self.email_dorks[:3]:
                dorks.append(f'"{primary_business}" "{location}" {email_dork}')
            
            # Phone-focused searches
            for phone_dork in self.phone_dorks[:3]:
                dorks.append(f'"{primary_business}" "{location}" {phone_dork}')
            
            # Contact page searches
            for contact_dork in self.contact_dorks[:3]:
                dorks.append(f'"{primary_business}" "{location}" {contact_dork}')
        
        # Advanced business discovery dorks
        primary_business = business_variations[0] if business_variations else business_type
        dorks.extend([
            f'"{primary_business}" "{location}" "hours" "address"',
            f'"{primary_business}" "{location}" "services" contact',
            f'"{primary_business}" "{location}" "about us" phone',
            f'"{primary_business}" "{location}" reviews rating',
            f'intitle:"{primary_business}" "{location}" intext:"phone"',
            f'site:*.com "{primary_business}" "{location}" contact',
            f'"{primary_business}" "{location}" -site:facebook.com -site:linkedin.com',
            f'"{primary_business}" "{location}" filetype:pdf contact',
        ])
        
        # Remove duplicates and shuffle for variety
        unique_dorks = list(set(dorks))
        random.shuffle(unique_dorks)
        
        logger.info(f"Generated {len(unique_dorks)} unique dorks for {business_type} in {location}")
        return unique_dorks
    
    def generate_email_hunting_dorks(self, business_name: str, domain: str = None) -> List[str]:
        """
        Generate dorks specifically for email hunting
        
        Args:
            business_name: Name of the business
            domain: Optional domain name to search
            
        Returns:
            List of email-focused dork queries
        """
        dorks = []
        
        if domain:
            # Domain-specific email searches
            dorks.extend([
                f'site:{domain} "email:" OR "e-mail:" OR "contact:"',
                f'site:{domain} "@{domain}"',
                f'site:{domain} filetype:pdf "@"',
                f'site:{domain} intext:"mailto:"',
                f'site:{domain} "contact us" email',
                f'"{business_name}" "@{domain}"',
                f'"{business_name}" site:{domain} contact'
            ])
        
        # General email hunting
        dorks.extend([
            f'"{business_name}" email contact',
            f'"{business_name}" "@" phone',
            f'"{business_name}" "mailto:" contact',
            f'"{business_name}" "e-mail:" phone',
            f'"{business_name}" intext:"@" contact',
            f'"{business_name}" filetype:pdf "@"',
            f'"{business_name}" "contact information" email'
        ])
        
        return dorks
    
    def generate_social_media_dorks(self, business_name: str, location: str) -> List[str]:
        """
        Generate dorks for finding social media profiles
        
        Args:
            business_name: Name of the business
            location: Business location
            
        Returns:
            List of social media focused dorks
        """
        dorks = []
        
        social_platforms = [
            'facebook.com',
            'linkedin.com',
            'twitter.com',
            'instagram.com',
            'youtube.com',
            'tiktok.com'
        ]
        
        for platform in social_platforms:
            dorks.extend([
                f'site:{platform} "{business_name}"',
                f'site:{platform} "{business_name}" "{location}"',
                f'site:{platform} "{business_name}" contact',
                f'site:{platform} "{business_name}" about'
            ])
        
        return dorks
    
    def generate_advanced_discovery_dorks(self, business_type: str, location: str) -> List[str]:
        """
        Generate advanced dorks for deep business discovery
        
        Args:
            business_type: Type of business
            location: Location to search
            
        Returns:
            List of advanced discovery dorks
        """
        variations = self._get_business_variations(business_type)
        primary = variations[0] if variations else business_type
        
        advanced_dorks = [
            # Government and licensing searches
            f'site:gov "{primary}" "{location}" license',
            f'site:gov "{primary}" "{location}" permit',
            f'site:gov "{primary}" "{location}" registration',
            
            # Professional directory searches
            f'inurl:directory "{primary}" "{location}"',
            f'inurl:listings "{primary}" "{location}"',
            f'inurl:professionals "{primary}" "{location}"',
            
            # Review and rating platform searches
            f'site:yelp.com "{primary}" "{location}"',
            f'site:google.com/maps "{primary}" "{location}"',
            f'site:bbb.org "{primary}" "{location}"',
            f'site:angie.com "{primary}" "{location}"',
            
            # Industry-specific searches
            f'"{primary}" "{location}" association member',
            f'"{primary}" "{location}" certified licensed',
            f'"{primary}" "{location}" "years experience"',
            f'"{primary}" "{location}" "established" "since"',
            
            # Contact and service searches
            f'"{primary}" "{location}" "emergency" "24/7"',
            f'"{primary}" "{location}" "free consultation"',
            f'"{primary}" "{location}" "call now" "book"',
            f'"{primary}" "{location}" "appointment" "schedule"',
            
            # Local business searches
            f'"{primary}" "{location}" "locally owned"',
            f'"{primary}" "{location}" "family business"',
            f'"{primary}" "{location}" "serving" area',
            
            # Exclusion searches (avoid ads/spam)
            f'"{primary}" "{location}" -site:ads.com -site:spam.com -inurl:ad',
            f'"{primary}" "{location}" -"click here" -"buy now" -advertisement'
        ]
        
        return advanced_dorks
    
    def _get_business_variations(self, business_type: str) -> List[str]:
        """
        Get variations and synonyms for a business type
        
        Args:
            business_type: Original business type
            
        Returns:
            List of business type variations
        """
        # Normalize the business type
        normalized = business_type.lower().strip()
        
        # Check for exact matches in mapping
        if normalized in self.business_type_mapping:
            variations = [normalized] + self.business_type_mapping[normalized]
        else:
            # Check for partial matches
            variations = [normalized]
            for key, values in self.business_type_mapping.items():
                if normalized in key or key in normalized:
                    variations.extend([key] + values)
                    break
                # Check if any variation matches
                for variation in values:
                    if normalized in variation or variation in normalized:
                        variations.extend([key] + values)
                        break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for variation in variations:
            if variation not in seen:
                seen.add(variation)
                unique_variations.append(variation)
        
        return unique_variations[:5]  # Return top 5 variations
    
    def create_search_strategy(self, business_type: str, location: str, 
                             max_queries: int = 20) -> Dict[str, List[str]]:
        """
        Create a comprehensive search strategy with prioritized dorks
        
        Args:
            business_type: Type of business to search for
            location: Location to search in
            max_queries: Maximum number of queries per category
            
        Returns:
            Dictionary with categorized search queries
        """
        strategy = {
            'primary_business': [],
            'contact_focused': [],
            'email_hunting': [],
            'social_media': [],
            'advanced_discovery': []
        }
        
        # Generate all types of dorks
        business_dorks = self.generate_business_dorks(business_type, location, include_contact=False)
        contact_dorks = self.generate_business_dorks(business_type, location, include_contact=True)
        social_dorks = self.generate_social_media_dorks(business_type, location)
        advanced_dorks = self.generate_advanced_discovery_dorks(business_type, location)
        
        # Categorize and limit queries
        strategy['primary_business'] = business_dorks[:max_queries]
        strategy['contact_focused'] = [d for d in contact_dorks if any(
            contact_term in d for contact_term in ['email', 'phone', 'contact', 'mailto']
        )][:max_queries]
        strategy['social_media'] = social_dorks[:max_queries]
        strategy['advanced_discovery'] = advanced_dorks[:max_queries]
        
        # Create email hunting queries for generic business
        strategy['email_hunting'] = self.generate_email_hunting_dorks(business_type)[:max_queries]
        
        logger.info(f"Created search strategy with {sum(len(queries) for queries in strategy.values())} total queries")
        return strategy
    
    def get_random_dork(self, business_type: str, location: str) -> str:
        """
        Get a random dork for variety in scraping
        
        Args:
            business_type: Type of business
            location: Location
            
        Returns:
            Random dork query
        """
        all_dorks = self.generate_business_dorks(business_type, location)
        return random.choice(all_dorks) if all_dorks else f'"{business_type}" "{location}"'