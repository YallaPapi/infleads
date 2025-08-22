#!/usr/bin/env python3
"""
Test script to verify MultiProvider and provider integration fixes
"""

import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from providers.multi_provider import MultiProvider

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_query_formats():
    """Test different query formats"""
    provider = MultiProvider()
    
    test_queries = [
        "restaurants in New York",  # Combined format
        "dentists in Miami",       # Combined format
        "coffee shops",            # Keyword only
        "lawyers in Las Vegas",    # Combined format
        "",                        # Empty query
        "   ",                     # Whitespace only
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: '{query}'")
        print(f"{'='*60}")
        
        try:
            results = provider.fetch_places(query, limit=5)
            print(f"Results count: {len(results)}")
            
            if results:
                # Show first result with metadata
                result = results[0]
                print(f"Sample result:")
                print(f"  Name: {result.get('name', 'N/A')}")
                print(f"  Source: {result.get('source', 'N/A')}")
                print(f"  Search Keyword: {result.get('search_keyword', 'N/A')}")
                print(f"  Search Location: {result.get('search_location', 'N/A')}")
                print(f"  Full Query: {result.get('full_query', 'N/A')}")
            else:
                print("No results returned")
                
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

def test_query_validation():
    """Test query validation method"""
    provider = MultiProvider()
    
    test_queries = [
        "restaurants in New York",
        "dentists",
        "",
        "   ",
        "lawyers in ",
        " in Miami"
    ]
    
    print(f"\n{'='*60}")
    print("Testing Query Validation")
    print(f"{'='*60}")
    
    for query in test_queries:
        validation = provider._validate_query_format(query)
        print(f"\nQuery: '{query}'")
        print(f"  Format Type: {validation['format_type']}")
        print(f"  Is Valid: {validation['is_valid']}")
        print(f"  Issues: {validation['issues']}")

if __name__ == "__main__":
    print("Testing MultiProvider Integration Fixes")
    print("=" * 80)
    
    # Test query validation
    test_query_validation()
    
    # Test actual queries (limit to avoid too much output)
    test_query_formats()
    
    print("\n" + "=" * 80)
    print("Test completed!")