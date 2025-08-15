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
    
    # Apify Google Maps Scraper actor ID (use the popular one)
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
            # Prepare input for the actor (using correct field names)
            run_input = {
                "searchStringsArray": [query],  # Correct field name
                "maxCrawledPlacesPerSearch": limit,
                "language": "en",
                "scrapeReviews": False,  # We don't need individual reviews
                "scrapePhotos": False,   # We just need count
                "additionalInfo": True,   # Get all available info
                "deeperCityScrape": False,
                "skipClosedPlaces": False
            }
            
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
        
        # Try to extract email from various possible fields
        email = item.get('email', 'NA')
        if email == 'NA':
            # Sometimes email might be in additionalInfo or other fields
            additional_info = item.get('additionalInfo', {})
            email = additional_info.get('email', 'NA')
        
        # If still no email, it might be in the raw data under different names
        if email == 'NA':
            for field in ['contactEmail', 'businessEmail', 'contact']:
                if field in item and '@' in str(item[field]):
                    email = item[field]
                    break
        
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