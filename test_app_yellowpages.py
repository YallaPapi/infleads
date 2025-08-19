#!/usr/bin/env python3
"""
Test Yellow Pages integration with app.py
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import app components
from src.providers.yellowpages_api_provider import YellowPagesAPIProvider

def test_app_integration():
    """Test Yellow Pages as it's used in app.py"""
    
    print("Testing Yellow Pages integration as used in app.py...")
    print("=" * 60)
    
    # This is how app.py uses it
    providers = ['yellowpages']
    query = "dentists"
    location = "miami"
    limit = 10
    
    provider_results = {}
    
    # Yellow Pages
    if 'yellowpages' in providers:
        try:
            print(f"\nSearching Yellow Pages for '{query}' in '{location}'...")
            yp_provider = YellowPagesAPIProvider()
            yp_results = yp_provider.search_businesses(query, location, limit)
            provider_results['yellowpages'] = {
                'count': len(yp_results),
                'results': yp_results
            }
            print(f"✓ Yellow Pages found {len(yp_results)} results")
            
            # Display first few results
            for i, result in enumerate(yp_results[:3], 1):
                print(f"\n  Result {i}:")
                print(f"    Name: {result.get('name')}")
                print(f"    Address: {result.get('address')}")
                print(f"    Phone: {result.get('phone')}")
                
        except Exception as e:
            print(f"✗ Yellow Pages provider error: {e}")
            provider_results['yellowpages'] = {'error': str(e), 'count': 0}
    
    # Save results
    with open('app_yellowpages_test.json', 'w') as f:
        json.dump(provider_results, f, indent=2)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    
    if 'yellowpages' in provider_results:
        yp = provider_results['yellowpages']
        if 'error' in yp:
            print(f"Yellow Pages: ERROR - {yp['error']}")
        else:
            print(f"Yellow Pages: {yp['count']} results found")
    
    print("\nResults saved to: app_yellowpages_test.json")

if __name__ == "__main__":
    test_app_integration()