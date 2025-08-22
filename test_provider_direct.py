#!/usr/bin/env python3
"""Direct test of provider functionality"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers.openstreetmap_provider import OpenStreetMapProvider
from src.providers.pure_scraper import PureWebScraper
from src.providers.multi_provider import MultiProvider

print("\n=== DIRECT PROVIDER TEST ===\n")

# Test 1: OpenStreetMap Provider
print("1. Testing OpenStreetMap Provider:")
print("-" * 40)
try:
    osm = OpenStreetMapProvider()
    query = "restaurants in Manhattan, New York"
    print(f"Query: '{query}'")
    results = osm.fetch_places(query, limit=3)
    print(f"Results: {len(results)} found")
    for i, r in enumerate(results[:3], 1):
        print(f"  {i}. {r.get('name', 'N/A')}")
        print(f"     Address: {r.get('address', 'N/A')}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing Pure Web Scraper:")
print("-" * 40)
try:
    pure = PureWebScraper()
    query = "coffee shops in San Francisco"
    print(f"Query: '{query}'")
    results = pure.fetch_places(query, limit=3)
    print(f"Results: {len(results)} found")
    for i, r in enumerate(results[:3], 1):
        print(f"  {i}. {r.get('name', 'N/A')}")
        print(f"     Address: {r.get('address', 'N/A')}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing MultiProvider (auto):")
print("-" * 40)
try:
    multi = MultiProvider()
    query = "dentists in Chicago"
    print(f"Query: '{query}'")
    results = multi.fetch_places(query, limit=3)
    print(f"Results: {len(results)} found")
    for i, r in enumerate(results[:3], 1):
        print(f"  {i}. {r.get('name', 'N/A')}")
        print(f"     Address: {r.get('address', 'N/A')}")
        print(f"     Source: {r.get('source', 'N/A')}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n=== END TEST ===")