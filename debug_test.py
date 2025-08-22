#!/usr/bin/env python3
"""
Direct test of the OpenStreetMap provider to debug query processing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.providers.openstreetmap_provider import OpenStreetMapProvider
from src.providers.multi_provider import MultiProvider

def test_osm_directly():
    """Test OpenStreetMap provider directly"""
    print("=== Testing OpenStreetMap Provider Directly ===")
    
    # Test with location
    osm = OpenStreetMapProvider()
    
    test_queries = [
        "restaurants in Austin",
        "coffee shops in Austin, TX",
        "pizza in New York",
        "lawyers in Chicago"
    ]
    
    for query in test_queries:
        print(f"\n--- Testing query: '{query}' ---")
        try:
            results = osm.fetch_places(query, limit=5)
            print(f"Results: {len(results)} places found")
            
            if results:
                sample = results[0]
                print(f"Sample result: {sample.get('name', 'Unknown')} - {sample.get('city', 'No city')}")
                print(f"Search metadata: keyword='{sample.get('search_keyword')}', location='{sample.get('search_location')}'")
            else:
                print("No results found")
                
        except Exception as e:
            print(f"Error: {e}")

def test_multi_provider():
    """Test MultiProvider"""
    print("\n=== Testing MultiProvider ===")
    
    mp = MultiProvider()
    
    test_queries = [
        "restaurants in Austin",
        "coffee shops in Austin, TX"
    ]
    
    for query in test_queries:
        print(f"\n--- Testing query: '{query}' ---")
        try:
            results = mp.fetch_places(query, limit=5)
            print(f"Results: {len(results)} places found")
            
            if results:
                sample = results[0]
                print(f"Sample result: {sample.get('name', 'Unknown')} - {sample.get('city', 'No city')}")
                print(f"Source: {sample.get('source', 'Unknown')}")
            else:
                print("No results found")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_osm_directly()
    test_multi_provider()