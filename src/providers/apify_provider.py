"""
Apify provider for Google Maps data
"""

import os
import logging
from typing import List, Dict, Any
from apify_client import ApifyClient
from .base import BaseProvider

logger = logging.getLogger(__name__)


class ApifyProvider(BaseProvider):
    """Provider for fetching Google Maps data via Apify"""
    
    # Apify Google Maps Scraper actor ID (use the ID not the name!)
    ACTOR_ID = "nwua9Gu5YrADL7ZDj"  # Google Maps Scraper by Compass
    
    def __init__(self):
        """Initialize Apify client"""
        api_key = os.getenv('APIFY_API_KEY')
        if not api_key:
            raise ValueError("APIFY_API_KEY not found in environment variables")
        
        self.client = ApifyClient(api_key)
        logger.info("Apify provider initialized")
    
    def fetch_places(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch business leads from Google Maps via Apify
        
        Args:
            query: Search query (e.g., "dentists in Miami")
            limit: Maximum number of results to fetch
            
        Returns:
            List of dictionaries containing lead data
        """
        logger.info(f"Fetching places from Apify: query='{query}', limit={limit}")
        
        try:
            # Split query into keyword and location if "in" is present
            keyword = query
            location = None
            if " in " in query.lower():
                parts = query.split(" in ", 1)
                keyword = parts[0].strip()
                location = parts[1].strip()
                logger.info(f"Split query: keyword='{keyword}', location='{location}'")
            
            # Prepare input for the actor (correct parameters for compass/crawler-google-places)
            run_input = {
                "searchStringsArray": [keyword],  # Just the keyword, no location
                "maxCrawledPlacesPerSearch": limit,
                "language": "en",
                "skipClosedPlaces": False,
                "scrapePlaceDetailPage": False,
                "includeOpeningHours": True,
                "maxImages": 0,
                "maxReviews": 0,
                # DISABLE EMAIL ENRICHMENT - IT'S TOO EXPENSIVE!
                "scrapeContacts": False,  # This is for additional contact scraping
                "maximumLeadsEnrichmentRecords": 0,  # DISABLED - costs way too much!
                # Filter to businesses with websites (better email hit rate)
                "website": "allPlaces",  # Can be "allPlaces", "withWebsite", or "withoutWebsite"
                # Additional parameters
                "scrapeDirectories": False,
                "includeWebResults": False,
                "searchMatching": "all"
            }
            
            # Add location if we have one
            if location:
                run_input["locationQuery"] = location
            
            # Run the actor and wait for it to finish
            logger.info("Starting Apify actor run...")
            run = self.client.actor(self.ACTOR_ID).call(run_input=run_input)
            
            # Fetch results from the run's dataset
            logger.info("Fetching results from dataset...")
            items = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                items.append(self._transform_apify_result(item))
                if len(items) >= limit:
                    break
            
            logger.info(f"Successfully fetched {len(items)} results from Apify")
            return items
            
        except Exception as e:
            logger.error(f"Error fetching data from Apify: {e}")
            raise
    
    def _extract_emails(self, item: Dict[str, Any]) -> str:
        """
        Extract emails from all possible field locations in Apify result
        
        Args:
            item: Raw item from Apify
            
        Returns:
            Email address or 'NA' if not found
        """
        emails = []
        
        # 1. PRIMARY SOURCE: leadsEnrichment field (when maximumLeadsEnrichmentRecords > 0)
        if 'leadsEnrichment' in item:
            enrichment = item['leadsEnrichment']
            
            # It can be a list of lead records
            if isinstance(enrichment, list):
                for lead in enrichment:
                    if isinstance(lead, dict):
                        # Check for email field
                        if lead.get('email'):
                            emails.append(lead['email'])
                        # Check for emails field (list or string)
                        elif lead.get('emails'):
                            lead_emails = lead['emails']
                            if isinstance(lead_emails, list):
                                emails.extend(lead_emails)
                            elif isinstance(lead_emails, str):
                                emails.append(lead_emails)
            
            # It can be a dict with emails field
            elif isinstance(enrichment, dict):
                if enrichment.get('email'):
                    emails.append(enrichment['email'])
                if enrichment.get('emails'):
                    enrichment_emails = enrichment['emails']
                    if isinstance(enrichment_emails, list):
                        emails.extend(enrichment_emails)
                    elif isinstance(enrichment_emails, str):
                        emails.append(enrichment_emails)
        
        # 2. Check top-level email fields (fallback)
        for field in ('email', 'contactEmail'):
            if item.get(field):
                emails.append(item[field])
        
        for field in ('emails', 'companyEmails'):
            value = item.get(field)
            if isinstance(value, list):
                emails.extend(value)
            elif isinstance(value, str):
                emails.append(value)
        
        # 3. Check nested contact info (fallback)
        contacts = item.get('contactInfo') or item.get('contacts') or {}
        if isinstance(contacts, dict):
            for field in ('email', 'emails', 'companyEmails'):
                value = contacts.get(field)
                if isinstance(value, list):
                    emails.extend(value)
                elif isinstance(value, str):
                    emails.append(value)
        
        # Clean and deduplicate
        clean_emails = sorted({e for e in emails if isinstance(e, str) and '@' in e})
        
        if clean_emails:
            logger.info(f"Found email(s) for {item.get('title', 'Unknown')}: {clean_emails[0]}")
            return clean_emails[0]  # Return first email
        
        return 'NA'
    
    def _transform_apify_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Apify result to our standard format
        
        Args:
            item: Raw item from Apify
            
        Returns:
            Transformed dictionary with standard fields
        """
        # Extract social media links if available
        social_links = []
        if item.get('facebookUrl'):
            social_links.append(item['facebookUrl'])
        if item.get('instagramUrl'):
            social_links.append(item['instagramUrl'])
        if item.get('twitterUrl'):
            social_links.append(item['twitterUrl'])
        if item.get('linkedinUrl'):
            social_links.append(item['linkedinUrl'])
        
        social_media = ', '.join(social_links) if social_links else 'NA'
        
        # Format reviews information
        reviews_info = 'NA'
        if item.get('reviewsCount') and item.get('reviewsAverage'):
            reviews_info = f"{item['reviewsAverage']:.1f} stars ({item['reviewsCount']} reviews)"
        elif item.get('reviewsCount'):
            reviews_info = f"{item['reviewsCount']} reviews"
        
        # Get image count
        image_count = 'NA'
        if item.get('imagesCount'):
            image_count = str(item['imagesCount'])
        elif item.get('images'):
            image_count = str(len(item['images']))
        
        # Check if business is claimed (this might not always be available)
        claimed = item.get('claimedByOwnerAt') is not None or item.get('isClaimedByOwner', False)
        
        # Extract email using comprehensive logic
        email = self._extract_emails(item)
        
        return {
            'Name': item.get('title', 'NA'),
            'Address': item.get('address', item.get('streetAddress', 'NA')),
            'Phone': item.get('phone', item.get('phoneNumber', 'NA')),
            'Email': email,  # Added email field
            'Website': item.get('website', item.get('url', 'NA')),
            'SocialMediaLinks': social_media,
            'Reviews': reviews_info,
            'Images': image_count,
            'Rating': item.get('reviewsAverage', 0),
            'ReviewCount': item.get('reviewsCount', 0),
            'GoogleBusinessClaimed': claimed,
            # Keep raw data for scoring
            '_raw': item
        }