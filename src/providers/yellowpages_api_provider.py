"""
Yellow Pages API Provider - now just wraps the working YellowPagesProvider
Previously used a hosted API, now uses the working provider with ScrapeGraph AI
"""

import logging
from typing import List, Dict
from .yellowpages_provider import YellowPagesProvider

logger = logging.getLogger(__name__)

class YellowPagesAPIProvider:
    """
    Yellow Pages API provider - wraps the working YellowPagesProvider
    This ensures compatibility with existing code that uses YellowPagesAPIProvider
    """
    
    def __init__(self):
        # Just use the working YellowPagesProvider
        self.provider = YellowPagesProvider()
        logger.info("YellowPagesAPIProvider initialized (using YellowPagesProvider with ScrapeGraph AI)")
        
    def search_businesses(self, query: str, location: str = None, limit: int = 20) -> List[Dict]:
        """
        Search for businesses using the working YellowPagesProvider
        """
        # Simply delegate to the working provider
        return self.provider.search_businesses(query, location, limit)
    
    def test_connection(self) -> Dict:
        """
        Test the Yellow Pages connection
        
        Returns:
            dict: Test results with status and message
        """
        try:
            # Test with a simple search
            results = self.search_businesses("restaurants in new york", limit=1)
            
            if results:
                return {
                    'success': True,
                    'message': f'Yellow Pages connection successful. Provider is working.',
                    'setup_required': False
                }
            else:
                return {
                    'success': False,
                    'message': 'Yellow Pages returned no results for test query',
                    'setup_required': False
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Yellow Pages test failed: {str(e)}',
                'setup_required': False
            }
    
    def is_configured(self) -> bool:
        """Yellow Pages is always available (no API key required)"""
        return True