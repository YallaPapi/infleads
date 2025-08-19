#!/usr/bin/env python3
"""
Test script to debug Yellow Pages extraction
"""

import sys
import os
import logging
from urllib.parse import quote_plus

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import Botasaurus
from botasaurus.request import request, Request
from botasaurus.soupify import soupify

@request(max_retry=1)
def test_extraction(request_obj: Request, data):
    """Test Yellow Pages extraction with debugging"""
    
    # Build URL
    search_term = quote_plus(data['search_term'])
    location = quote_plus(data['location'])
    url = f"https://www.yellowpages.com/search?search_terms={search_term}&geo_location_terms={location}"
    
    print(f"\nFetching: {url}")
    response = request_obj.get(url)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        soup = soupify(response)
        
        # Find all result divs
        results = soup.find_all("div", class_="result")
        print(f"Found {len(results)} result divs")
        
        if results:
            # Analyze first result in detail
            first_result = results[0]
            print("\n=== FIRST RESULT STRUCTURE ===")
            
            # Try to find business name
            name_elem = first_result.find("a", class_="business-name")
            if name_elem:
                print(f"✓ Business name found: {name_elem.get_text(strip=True)}")
            else:
                print("✗ No business-name anchor found")
                # Try alternative selectors
                h2 = first_result.find("h2")
                if h2:
                    print(f"  Found h2: {h2.get_text(strip=True)[:50]}...")
                    a_in_h2 = h2.find("a")
                    if a_in_h2:
                        print(f"  Anchor in h2: {a_in_h2.get_text(strip=True)}")
            
            # Try to find phone
            phone_elem = first_result.find("div", class_="phones")
            if phone_elem:
                print(f"✓ Phone found: {phone_elem.get_text(strip=True)}")
            else:
                phone_elem = first_result.find("div", class_="phone")
                if phone_elem:
                    print(f"✓ Phone (alt) found: {phone_elem.get_text(strip=True)}")
                else:
                    print("✗ No phone div found")
            
            # Try to find address
            address_elem = first_result.find("div", class_="street-address")
            if address_elem:
                print(f"✓ Street address found: {address_elem.get_text(strip=True)}")
            else:
                print("✗ No street-address div found")
            
            locality_elem = first_result.find("div", class_="locality")
            if locality_elem:
                print(f"✓ Locality found: {locality_elem.get_text(strip=True)}")
            else:
                print("✗ No locality div found")
                
            # Alternative address selector
            adr_elem = first_result.find("div", class_="adr")
            if adr_elem:
                print(f"✓ Address (adr) found: {adr_elem.get_text(strip=True)}")
            
            # Debug: print all classes in the result
            print("\n=== ALL DIV CLASSES IN FIRST RESULT ===")
            all_divs = first_result.find_all("div", class_=True)
            unique_classes = set()
            for div in all_divs:
                classes = div.get("class", [])
                for cls in classes:
                    unique_classes.add(cls)
            print(f"Unique classes: {sorted(unique_classes)}")
            
            # Print raw HTML snippet
            print("\n=== RAW HTML SNIPPET (first 1000 chars) ===")
            print(str(first_result)[:1000])
            
        return len(results)
    
    return 0

if __name__ == "__main__":
    # Test data
    test_data = {
        'search_term': 'restaurants',
        'location': 'New York'
    }
    
    print("Testing Yellow Pages extraction with detailed debugging...")
    print("=" * 60)
    
    # Run the test
    result_count = test_extraction(test_data)
    print(f"\n=== SUMMARY ===")
    print(f"Total results found: {result_count}")