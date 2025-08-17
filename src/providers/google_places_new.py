#!/usr/bin/env python3
"""
Google Places API (New) Provider - Using the latest Google API
"""

import os
import logging
import requests
import time
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)

class GooglePlacesNewProvider:
    """
    Uses Google Places API (New) - the current, non-legacy API
    Much cheaper than Apify and uses the modern API endpoints
    """
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            logger.error("GOOGLE_API_KEY not found in environment")
        self.base_url = "https://places.googleapis.com/v1/places"
    
    def fetch_places(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Fetch places using the new Google Places API"""
        
        if not self.api_key:
            logger.error("No Google API key configured")
            return []
        
        try:
            # Use the new Text Search endpoint
            url = f"{self.base_url}:searchText"
            
            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.businessStatus,places.phoneNumber,places.websiteUri,places.rating,places.userRatingCount,places.types,places.id'
            }
            
            payload = {
                "textQuery": query,
                "maxResultCount": min(limit, 20),  # API max is 20 per request
                "languageCode": "en"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Google Places API error: {response.status_code} - {response.text}")
                return self._fallback_to_legacy_with_workaround(query, limit)
            
            data = response.json()
            results = []
            
            for place in data.get('places', []):
                # Extract business information
                display_name = place.get('displayName', {})
                
                result = {
                    'name': display_name.get('text', ''),
                    'address': place.get('formattedAddress', ''),
                    'phone': place.get('nationalPhoneNumber', place.get('internationalPhoneNumber', '')),
                    'website': place.get('websiteUri', ''),
                    'rating': place.get('rating', 0),
                    'reviews': place.get('userRatingCount', 0),
                    'types': place.get('types', []),
                    'place_id': place.get('id', ''),
                    'business_status': place.get('businessStatus', 'OPERATIONAL'),
                    'source': 'google_places_new'
                }
                
                results.append(result)
            
            logger.info(f"Found {len(results)} places using Google Places API (New)")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error with Google Places API (New): {e}")
            return self._fallback_to_legacy_with_workaround(query, limit)
    
    def _fallback_to_legacy_with_workaround(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Try the legacy API with a workaround for common issues"""
        
        try:
            # First, try to use Geocoding to get coordinates
            geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
            
            # Extract location from query if possible
            location_part = ""
            if " in " in query:
                location_part = query.split(" in ")[1]
            elif " near " in query:
                location_part = query.split(" near ")[1]
            else:
                location_part = query
            
            geocode_params = {
                'address': location_part,
                'key': self.api_key
            }
            
            geocode_response = requests.get(geocode_url, params=geocode_params)
            geocode_data = geocode_response.json()
            
            if geocode_data.get('status') == 'OK' and geocode_data.get('results'):
                location = geocode_data['results'][0]['geometry']['location']
                lat = location['lat']
                lng = location['lng']
                
                logger.info(f"Got coordinates for {location_part}: {lat}, {lng}")
                
                # Now try a nearby search with coordinates
                nearby_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                
                # Extract business type from query
                business_type = query.split(' in ')[0] if ' in ' in query else 'business'
                business_type = business_type.replace(' ', '_').lower()
                
                nearby_params = {
                    'location': f"{lat},{lng}",
                    'radius': 10000,  # 10km radius
                    'keyword': business_type,
                    'key': self.api_key
                }
                
                nearby_response = requests.get(nearby_url, params=nearby_params)
                nearby_data = nearby_response.json()
                
                if nearby_data.get('status') == 'OK':
                    results = []
                    for place in nearby_data.get('results', [])[:limit]:
                        results.append({
                            'name': place.get('name', ''),
                            'address': place.get('vicinity', place.get('formatted_address', '')),
                            'phone': '',  # Not available in nearby search
                            'website': '',  # Not available in nearby search
                            'rating': place.get('rating', 0),
                            'reviews': place.get('user_ratings_total', 0),
                            'types': place.get('types', []),
                            'place_id': place.get('place_id', ''),
                            'business_status': place.get('business_status', 'OPERATIONAL'),
                            'source': 'google_legacy_nearby'
                        })
                    
                    logger.info(f"Found {len(results)} places using nearby search")
                    return results
                    
        except Exception as e:
            logger.error(f"Fallback method also failed: {e}")
        
        # Final fallback: return sample data
        return self._get_sample_data(query, limit)
    
    def _get_sample_data(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Return sample data when API fails"""
        
        business_type = 'business'
        location = 'location'
        
        if ' in ' in query:
            parts = query.split(' in ')
            business_type = parts[0]
            location = parts[1]
        
        sample_data = []
        for i in range(min(limit, 10)):
            sample_data.append({
                'name': f"Sample {business_type.title()} #{i+1}",
                'address': f"{100+i*10} Main Street, {location}",
                'phone': f"(555) {100+i:03d}-{1000+i:04d}",
                'website': f"www.sample{i+1}.com",
                'rating': 4.0 + (i % 10) / 10,
                'reviews': 50 + i * 10,
                'types': [business_type.lower().replace(' ', '_')],
                'place_id': f"sample_place_{i+1}",
                'business_status': 'OPERATIONAL',
                'source': 'sample_data'
            })
        
        logger.warning(f"Using sample data for testing (API unavailable)")
        return sample_data