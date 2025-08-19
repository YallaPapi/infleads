#!/usr/bin/env python3
"""
Test Yellow Pages with real business searches
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from providers.yellowpages_provider import YellowPagesProvider
import json

def test_real_searches():
    """Test with various real business searches"""
    yp = YellowPagesProvider()
    
    test_queries = [
        ("dentists in miami", 5),
        ("law firms in chicago", 5),
        ("auto repair shops in dallas", 5),
        ("restaurants in san francisco", 5),
        ("hair salons in atlanta", 5)
    ]
    
    all_results = {}
    
    for query, limit in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: {query} (limit: {limit})")
        print('='*60)
        
        results = yp.search_businesses(query, limit=limit)
        
        if results:
            print(f"✓ Found {len(results)} businesses")
            # Show first result details
            if results:
                first = results[0]
                print(f"\nFirst result:")
                print(f"  Name: {first.get('name')}")
                print(f"  Address: {first.get('address')}")
                print(f"  Phone: {first.get('phone')}")
                print(f"  Website: {first.get('website', 'N/A')}")
                print(f"  Categories: {', '.join(first.get('categories', []))}")
                print(f"  Years in business: {first.get('years_in_business', 'N/A')}")
        else:
            print(f"✗ No results found")
        
        all_results[query] = results
    
    # Save all results to a file
    with open('yellowpages_real_test_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    total_businesses = sum(len(results) for results in all_results.values())
    print(f"Total businesses found: {total_businesses}")
    print(f"Queries tested: {len(test_queries)}")
    print(f"Average results per query: {total_businesses / len(test_queries):.1f}")
    print("\nResults saved to: yellowpages_real_test_results.json")

if __name__ == "__main__":
    print("Testing Yellow Pages with real business searches...")
    print("Using Botasaurus for anti-bot bypass")
    test_real_searches()