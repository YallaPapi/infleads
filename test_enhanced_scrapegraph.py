"""
Enhanced test for ScrapeGraph AI with Yellow Pages
Testing different configurations to find what works
"""

import os
import json
import logging
from scrapegraphai.graphs import SmartScraperGraph

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_configuration_1_minimal():
    """Test 1: Minimal configuration (current approach)"""
    print("\n" + "="*60)
    print("TEST 1: Minimal Configuration (Current)")
    print("="*60)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ No OPENAI_API_KEY found")
        return None
    
    graph_config = {
        "llm": {"api_key": openai_key, "model": "openai/gpt-4o-mini"},
        "verbose": False,
        "headless": True
    }
    
    prompt = """
    Extract business information from this Yellow Pages search results page.
    For each business listing, get:
    - Business name
    - Phone number  
    - Address
    - Website (if available)
    
    Return the data as a structured JSON list.
    """
    
    url = "https://www.yellowpages.com/search?search_terms=restaurants&geo_location_terms=miami"
    
    try:
        smart_scraper = SmartScraperGraph(prompt=prompt, source=url, config=graph_config)
        result = smart_scraper.run()
        print(f"✅ Result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_configuration_2_enhanced_browser():
    """Test 2: Enhanced browser configuration"""
    print("\n" + "="*60)
    print("TEST 2: Enhanced Browser Configuration")
    print("="*60)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ No OPENAI_API_KEY found")
        return None
    
    graph_config = {
        "llm": {"api_key": openai_key, "model": "openai/gpt-4o-mini"},
        "verbose": True,  # Enable verbose logging
        "headless": True,
        "browser_config": {
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--disable-blink-features=AutomationControlled",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
        }
    }
    
    prompt = """
    You are scraping a Yellow Pages business directory search results page.
    
    Look for business listings on the page. Each business listing should have:
    - Business name (usually in a link or heading)
    - Phone number (usually formatted like (305) 123-4567)
    - Address (street address, city, state)
    - Website URL (if available)
    
    Extract this information and return as a JSON array like:
    [
        {
            "name": "Restaurant Name",
            "phone": "(305) 123-4567", 
            "address": "123 Main St, Miami, FL",
            "website": "https://example.com"
        }
    ]
    """
    
    url = "https://www.yellowpages.com/search?search_terms=restaurants&geo_location_terms=miami"
    
    try:
        smart_scraper = SmartScraperGraph(prompt=prompt, source=url, config=graph_config)
        result = smart_scraper.run()
        print(f"✅ Result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_configuration_3_different_model():
    """Test 3: Different LLM model"""
    print("\n" + "="*60)
    print("TEST 3: Different LLM Model (GPT-4)")
    print("="*60)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ No OPENAI_API_KEY found")
        return None
    
    graph_config = {
        "llm": {"api_key": openai_key, "model": "openai/gpt-4"},  # Use GPT-4 instead
        "verbose": True,
        "headless": True,
        "browser_config": {
            "args": ["--no-sandbox", "--disable-setuid-sandbox"]
        }
    }
    
    prompt = """
    This is a Yellow Pages search results page. Please extract ALL business listings from this page.
    
    For each business, find:
    1. Business name
    2. Phone number 
    3. Full address
    4. Website URL (if present)
    5. Business category/type
    
    Return as JSON array. If no businesses found, return empty array [].
    """
    
    url = "https://www.yellowpages.com/search?search_terms=restaurants&geo_location_terms=miami"
    
    try:
        smart_scraper = SmartScraperGraph(prompt=prompt, source=url, config=graph_config)
        result = smart_scraper.run()
        print(f"✅ Result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_configuration_4_simple_url():
    """Test 4: Try with a simpler URL"""
    print("\n" + "="*60)
    print("TEST 4: Simple URL Test")
    print("="*60)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ No OPENAI_API_KEY found")
        return None
    
    graph_config = {
        "llm": {"api_key": openai_key, "model": "openai/gpt-4o-mini"},
        "verbose": True,
        "headless": True
    }
    
    prompt = """
    Extract the title and main content from this webpage.
    """
    
    # Test with a simple webpage first
    url = "https://httpbin.org/html"
    
    try:
        smart_scraper = SmartScraperGraph(prompt=prompt, source=url, config=graph_config)
        result = smart_scraper.run()
        print(f"✅ Simple URL Result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_configuration_5_requests_html():
    """Test 5: Try with requests-html loader"""
    print("\n" + "="*60)
    print("TEST 5: Different Loader Strategy")
    print("="*60)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ No OPENAI_API_KEY found")
        return None
    
    graph_config = {
        "llm": {"api_key": openai_key, "model": "openai/gpt-4o-mini"},
        "verbose": True,
        "headless": False,  # Try non-headless first
        "loader_kwargs": {
            "wait_for": 2000,  # Wait 2 seconds for page to load
        }
    }
    
    prompt = """
    Extract business information from this Yellow Pages page. Look for:
    - Business names
    - Phone numbers
    - Addresses
    Return as structured data.
    """
    
    url = "https://www.yellowpages.com/search?search_terms=restaurants&geo_location_terms=miami"
    
    try:
        smart_scraper = SmartScraperGraph(prompt=prompt, source=url, config=graph_config)
        result = smart_scraper.run()
        print(f"✅ Result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("Enhanced ScrapeGraph AI Testing for Yellow Pages")
    print("Testing multiple configurations to find what works...")
    
    # Run all tests
    results = {}
    
    results['test_1_minimal'] = test_configuration_1_minimal()
    results['test_2_enhanced'] = test_configuration_2_enhanced_browser()
    results['test_3_gpt4'] = test_configuration_3_different_model()
    results['test_4_simple'] = test_configuration_4_simple_url()
    results['test_5_requests'] = test_configuration_5_requests_html()
    
    print("\n" + "="*60)
    print("SUMMARY OF ALL TESTS")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ SUCCESS" if result and result != {'content': 'NA'} and result != {'content': []} else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result and result != {'content': 'NA'} and result != {'content': []}:
            print(f"  Result: {str(result)[:100]}...")
    
    print("\nNext steps based on results:")
    print("- If any test succeeded, use that configuration")
    print("- If all failed, Yellow Pages may need selenium with more complex setup")
    print("- Consider fallback to requests-based scraping")