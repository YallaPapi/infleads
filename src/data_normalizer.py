"""
Data normalizer for lead data
"""

import logging
import pandas as pd
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalizes and cleans lead data for CSV output"""
    
    def normalize(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize lead data to ensure consistency
        
        Args:
            leads: List of raw lead dictionaries
            
        Returns:
            List of normalized lead dictionaries
        """
        logger.info(f"Normalizing {len(leads)} leads")
        normalized = []
        
        for lead in leads:
            normalized_lead = self._normalize_lead(lead)
            normalized.append(normalized_lead)
        
        logger.info(f"Normalized {len(normalized)} leads successfully")
        return normalized
    
    def _normalize_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single lead
        
        Args:
            lead: Raw lead dictionary
            
        Returns:
            Normalized lead dictionary
        """
        normalized = {}
        
        # Required fields with their defaults
        field_defaults = {
            'Name': 'NA',
            'Address': 'NA',
            'Phone': 'NA',
            'Website': 'NA',
            'SocialMediaLinks': 'NA',
            'Reviews': 'NA',
            'Images': 'NA',
            'Rating': 0,
            'ReviewCount': 0,
            'GoogleBusinessClaimed': False
        }
        
        for field, default in field_defaults.items():
            value = lead.get(field, default)
            
            # Handle None, empty strings, and NaN
            if value is None or value == '' or (isinstance(value, float) and pd.isna(value)):
                normalized[field] = default if field not in ['Rating', 'ReviewCount', 'GoogleBusinessClaimed'] else default
            else:
                # Clean and format the value
                if field in ['Name', 'Address', 'Phone', 'Website', 'SocialMediaLinks', 'Reviews', 'Images']:
                    # String fields - clean whitespace and handle commas
                    value = str(value).strip()
                    # Quote fields with commas for CSV safety
                    if ',' in value and not (value.startswith('"') and value.endswith('"')):
                        value = f'"{value}"'
                    normalized[field] = value if value else default
                else:
                    # Numeric/boolean fields
                    normalized[field] = value
        
        # Preserve raw data for scoring
        if '_raw' in lead:
            normalized['_raw'] = lead['_raw']
        
        return normalized