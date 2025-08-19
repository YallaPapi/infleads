#!/usr/bin/env python3
"""
Test script for Yellow Pages scraper functionality
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from providers.yellowpages_provider import YellowPagesProvider

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_yellowpages_scraper():
    """Test the Yellow Pages scraper"""
    print("Testing Yellow Pages Scraper...")
    
    # Initialize provider
    yp = YellowPagesProvider()
    
    # Test debug method first
    print("\n=== DEBUGGING HTML STRUCTURE ===")
    debug_output = yp.debug_html_structure("restaurants", "New York")
    print(debug_output)
    
    # Test search functionality
    print("\n=== TESTING SEARCH FUNCTIONALITY ===")
    try:
        results = yp.search_businesses("restaurants", "New York", limit=5)
        print(f"Found {len(results)} businesses")
        
        if results:
            print("\nFirst result:")
            first_result = results[0]
            for key, value in first_result.items():
                print(f"  {key}: {value}")
        else:
            print("No results found - this indicates the scraper is not working")
            
    except Exception as e:
        print(f"Error during search: {e}")
    
    # Test compatibility method
    print("\n=== TESTING COMPATIBILITY METHOD ===")
    try:
        results = yp.fetch_places("pizza in Los Angeles", limit=3)
        print(f"Compatibility method found {len(results)} businesses")
        
    except Exception as e:
        print(f"Error during compatibility test: {e}")

if __name__ == "__main__":
    test_yellowpages_scraper()