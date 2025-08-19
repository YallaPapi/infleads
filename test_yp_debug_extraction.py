#!/usr/bin/env python3
"""
Debug the _extract_business_info method
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from botasaurus.request import request, Request
from botasaurus.soupify import soupify
from providers.yellowpages_provider import YellowPagesProvider

@request
def test_extraction(request: Request, data):
    url = "https://www.yellowpages.com/search?search_terms=doctors&geo_location_terms=miami"
    print(f"Fetching: {url}")
    
    response = request.get(url)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        soup = soupify(response)
        results = soup.find_all("div", class_="result")
        print(f"Found {len(results)} results")
        
        if results:
            provider = YellowPagesProvider()
            
            # Test extraction on first result
            first_result = results[0]
            print("\n=== Testing _extract_business_info ===")
            
            # Debug what's in the result
            name_elem = first_result.find("a", class_="business-name")
            print(f"Name element found: {name_elem is not None}")
            if name_elem:
                print(f"Name text: {name_elem.get_text(strip=True)}")
            
            # Call the extraction method
            try:
                business = provider._extract_business_info(first_result)
                if business:
                    print("\n✓ Extraction successful!")
                    for key, value in business.items():
                        print(f"  {key}: {value}")
                else:
                    print("\n✗ Extraction returned None")
                    
                    # Debug why it failed
                    print("\nDebugging extraction failure...")
                    
                    # Check each selector
                    print("Checking selectors:")
                    print(f"  - business-name: {first_result.find('a', class_='business-name') is not None}")
                    print(f"  - h3: {first_result.find('h3') is not None}")
                    print(f"  - h2: {first_result.find('h2') is not None}")
                    
                    # Check alternative structure
                    h2_elem = first_result.find('h2')
                    if h2_elem:
                        print(f"  H2 content: {h2_elem.get_text(strip=True)[:50]}...")
                        h2_anchor = h2_elem.find('a')
                        if h2_anchor:
                            print(f"  H2 anchor: {h2_anchor.get_text(strip=True)}")
                    
            except Exception as e:
                print(f"\n✗ Extraction raised exception: {e}")
                import traceback
                traceback.print_exc()
        
        return len(results)
    return 0

if __name__ == "__main__":
    print("Testing Yellow Pages extraction method...")
    print("=" * 60)
    
    result_count = test_extraction({})
    print(f"\n=== SUMMARY ===")
    print(f"Total results: {result_count}")