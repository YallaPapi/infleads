"""
Test Botasaurus for Yellow Pages scraping
This demonstrates the core web scraping functionality (not desktop apps)
"""

from botasaurus.request import request, Request
from botasaurus.soupify import soupify
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@request(max_retry=10)
def test_yellowpages_with_botasaurus(request: Request, data):
    """
    Test Yellow Pages scraping using Botasaurus request module
    This uses smart HTTP requests with anti-bot detection bypass
    """
    search_term = data.get('search_term', 'doctors')
    location = data.get('location', 'miami')
    
    # Build Yellow Pages search URL
    url = f"https://www.yellowpages.com/search?search_terms={search_term}&geo_location_terms={location}"
    
    logger.info(f"Testing Botasaurus with URL: {url}")
    
    try:
        # Botasaurus automatically uses Google referrer and smart headers
        response = request.get(url)
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse with BeautifulSoup
            soup = soupify(response)
            
            # Find business results using Yellow Pages selectors
            results = soup.find_all("div", class_="result")
            logger.info(f"Found {len(results)} business results")
            
            businesses = []
            for result in results[:3]:  # Just test first 3
                try:
                    name_elem = result.find("a", class_="business-name")
                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        
                        phone_elem = result.find("div", class_="phone")
                        phone = phone_elem.get_text(strip=True) if phone_elem else "No phone"
                        
                        businesses.append({
                            "name": name,
                            "phone": phone,
                            "status": "success"
                        })
                except Exception as e:
                    logger.error(f"Error parsing result: {e}")
                    continue
            
            return {
                "status": "success",
                "url": url,
                "businesses_found": len(businesses),
                "businesses": businesses
            }
        else:
            return {
                "status": "failed",
                "status_code": response.status_code,
                "url": url
            }
            
    except Exception as e:
        logger.error(f"Botasaurus request failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "url": url
        }

if __name__ == "__main__":
    # Test data
    test_data = {
        'search_term': 'doctors',
        'location': 'miami'
    }
    
    print("Testing Botasaurus for Yellow Pages scraping...")
    print("This is pure web scraping - no desktop app involved")
    print("=" * 60)
    
    # Run the test
    result = test_yellowpages_with_botasaurus(test_data)
    
    print("Test Results:")
    print(f"Status: {result.get('status')}")
    print(f"URL: {result.get('url')}")
    
    if result.get('status') == 'success':
        print(f"✅ SUCCESS! Found {result.get('businesses_found')} businesses")
        for business in result.get('businesses', []):
            print(f"  - {business['name']} | {business['phone']}")
    else:
        print(f"❌ FAILED: {result.get('status_code', 'Unknown error')}")
        print(f"Error: {result.get('error', 'Unknown')}")