#!/usr/bin/env python3
"""
Debug YellowPagesAPIProvider
"""

import sys
import os
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from providers.yellowpages_api_provider import YellowPagesAPIProvider

def test_debug():
    """Debug test"""
    provider = YellowPagesAPIProvider()
    
    # Check if Botasaurus is being used
    print(f"Provider using Botasaurus: {provider.use_botasaurus}")
    print(f"Provider base URL: {provider.base_url}")
    
    # Simple test
    query = "dentists in miami"
    print(f"\nTesting: {query}")
    
    results = provider.search_businesses(query, limit=3)
    
    print(f"Results: {len(results)} found")
    if results:
        print("First result:", results[0])

if __name__ == "__main__":
    test_debug()