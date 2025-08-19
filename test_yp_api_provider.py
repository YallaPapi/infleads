#!/usr/bin/env python3
"""
Test the YellowPagesAPIProvider with Botasaurus
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from providers.yellowpages_api_provider import YellowPagesAPIProvider
import json

def test_api_provider():
    """Test the API provider"""
    provider = YellowPagesAPIProvider()
    
    test_queries = [
        ("dentists in miami", 5),
        ("restaurants in new york", 5),
        ("auto repair in dallas", 5)
    ]
    
    for query, limit in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: {query} (limit: {limit})")
        print('='*60)
        
        # Parse query if needed
        if ' in ' in query:
            parts = query.split(' in ')
            search_term = parts[0]
            location = parts[1]
        else:
            search_term = query
            location = "USA"
        
        results = provider.search_businesses(query, location=None, limit=limit)
        
        if results:
            print(f"✓ Found {len(results)} businesses")
            # Show first result
            if results:
                first = results[0]
                print(f"\nFirst result:")
                print(f"  Name: {first.get('name')}")
                print(f"  Address: {first.get('address')}")
                print(f"  Phone: {first.get('phone')}")
                print(f"  Website: {first.get('website', 'N/A')}")
        else:
            print(f"✗ No results found")

if __name__ == "__main__":
    print("Testing YellowPagesAPIProvider with Botasaurus...")
    test_api_provider()