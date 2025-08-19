#!/usr/bin/env python3
"""
Debug extraction with detailed error handling
"""

from botasaurus.request import request, Request
from botasaurus.soupify import soupify
import re

@request
def test_extraction_detailed(request: Request, data):
    url = "https://www.yellowpages.com/search?search_terms=doctors&geo_location_terms=miami"
    print(f"Fetching: {url}")
    
    response = request.get(url)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        soup = soupify(response)
        results = soup.find_all("div", class_="result")
        print(f"Found {len(results)} results")
        
        if results:
            # Test extraction on first result
            first_result = results[0]
            print("\n=== Extracting from first result ===")
            
            try:
                # Business name
                name_elem = first_result.find('a', class_='business-name')
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    print(f"✓ Name: {name}")
                else:
                    print("✗ No name found")
                    return 0
                
                # Phone
                phone = ''
                phone_elem = first_result.find('div', class_='phone')
                if phone_elem:
                    phone = phone_elem.get_text(strip=True)
                    phone = re.sub(r'[^\d\-\(\)\+\s]', '', phone).strip()
                    print(f"✓ Phone: {phone}")
                else:
                    print("✗ No phone found")
                
                # Address
                address = ''
                address_elem = first_result.find('div', class_='street-address')
                locality_elem = first_result.find('div', class_='locality')
                
                if address_elem:
                    address = address_elem.get_text(strip=True)
                if locality_elem:
                    if address:
                        address += ', '
                    address += locality_elem.get_text(strip=True)
                
                if not address:
                    adr_elem = first_result.find('div', class_='adr')
                    if adr_elem:
                        address = adr_elem.get_text(strip=True)
                
                print(f"✓ Address: {address if address else 'Not found'}")
                
                # Website
                website = ''
                website_elem = first_result.find('a', class_='track-visit-website')
                if website_elem:
                    website = website_elem.get('href', '')
                    print(f"✓ Website: {website}")
                else:
                    print("  Website: Not found")
                
                # Rating - this might be the problem
                rating = 0
                rating_elem = first_result.find('div', class_='ratings')
                if rating_elem:
                    print(f"  Rating element found, classes: {rating_elem.get('class')}")
                    try:
                        # This line might be causing issues
                        class_list = rating_elem.get('class', [])
                        if len(class_list) > 1:
                            rating_match = re.search(r'(\d+\.?\d*)', class_list[1])
                            if rating_match:
                                rating = float(rating_match.group(1))
                                print(f"✓ Rating: {rating}")
                        else:
                            print("  Rating: No rating class found")
                    except Exception as e:
                        print(f"✗ Rating extraction error: {e}")
                else:
                    print("  Rating: Element not found")
                
                # Categories
                categories = []
                cat_elem = first_result.find('div', class_='categories')
                if cat_elem:
                    cat_links = cat_elem.find_all('a')
                    categories = [link.get_text(strip=True) for link in cat_links]
                    print(f"✓ Categories: {categories}")
                else:
                    print("  Categories: Not found")
                
                # Years in business
                years_in_business = None
                info_elem = first_result.find('div', class_='years-in-business')
                if info_elem:
                    years_match = re.search(r'(\d+)', info_elem.get_text())
                    if years_match:
                        years_in_business = int(years_match.group(1))
                        print(f"✓ Years in business: {years_in_business}")
                else:
                    print("  Years in business: Not found")
                
                # Build result
                result = {
                    'name': name,
                    'address': address,
                    'phone': phone,
                    'website': website,
                    'rating': rating,
                    'reviews': 0,
                    'categories': categories,
                    'types': categories,
                    'place_id': f"yp_{name.replace(' ', '_')}_{address[:20] if address else 'unknown'}",
                    'business_status': 'OPERATIONAL',
                    'source': 'yellowpages',
                    'years_in_business': years_in_business
                }
                
                print("\n✓ Successfully created business dict!")
                return result
                
            except Exception as e:
                print(f"\n✗ Exception during extraction: {e}")
                import traceback
                traceback.print_exc()
                return None
    
    return None

if __name__ == "__main__":
    print("Testing Yellow Pages extraction with detailed debugging...")
    print("=" * 60)
    
    result = test_extraction_detailed({})
    if result:
        print("\n=== FINAL RESULT ===")
        for key, value in result.items():
            print(f"  {key}: {value}")