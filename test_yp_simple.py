#!/usr/bin/env python3
"""
Simple test of Botasaurus Yellow Pages scraping
"""

from botasaurus.request import request, Request
from botasaurus.soupify import soupify

@request
def scrape_yellowpages(request: Request, data):
    # Simple URL - no encoding needed since Botasaurus handles it
    url = f"https://www.yellowpages.com/search?search_terms=doctors&geo_location_terms=miami"
    print(f"Fetching: {url}")
    
    response = request.get(url)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        soup = soupify(response)
        results = soup.find_all("div", class_="result")
        print(f"Found {len(results)} results")
        
        # Extract first 3 businesses
        businesses = []
        for result in results[:3]:
            name_elem = result.find("a", class_="business-name")
            if name_elem:
                name = name_elem.get_text(strip=True)
                phone_elem = result.find("div", class_="phone")
                phone = phone_elem.get_text(strip=True) if phone_elem else "No phone"
                businesses.append({"name": name, "phone": phone})
                print(f"  - {name}: {phone}")
        
        return businesses
    return []

if __name__ == "__main__":
    print("Testing Yellow Pages with Botasaurus...")
    results = scrape_yellowpages({})
    print(f"\nExtracted {len(results)} businesses successfully!")