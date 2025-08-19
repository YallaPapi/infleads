"""
Test ScrapeGraph AI for Yellow Pages scraping
Real implementation - no demo data
"""

import os
from scrapegraphai.graphs import SmartScraperGraph

def test_scrapegraph_yellowpages():
    """
    Test ScrapeGraph AI with Yellow Pages
    """
    
    # Check if we have OpenAI API key (ScrapeGraph needs an LLM)
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ No OPENAI_API_KEY found in environment")
        print("ScrapeGraph AI requires an LLM provider")
        return None
    
    # Graph configuration for ScrapeGraph AI - MINIMAL headless config
    graph_config = {
        "llm": {
            "api_key": openai_key,
            "model": "openai/gpt-4o-mini",
        },
        "verbose": False,  # Reduce logging noise
        "headless": True   # ONLY this parameter - ScrapeGraph will handle the rest
    }
    
    # Define what we want to extract
    prompt = """
    Extract business information from this Yellow Pages search results page.
    For each business listing, get:
    - Business name
    - Phone number  
    - Address
    - Website (if available)
    - Business categories/types
    - Rating (if available)
    
    Return the data as a structured list.
    """
    
    # Test URL for doctors in Miami
    test_url = "https://www.yellowpages.com/search?search_terms=doctors&geo_location_terms=miami"
    
    print(f"Testing ScrapeGraph AI on: {test_url}")
    print("Prompt:", prompt[:100] + "...")
    
    try:
        # Create the smart scraper
        smart_scraper_graph = SmartScraperGraph(
            prompt=prompt,
            source=test_url,
            config=graph_config
        )
        
        # Run the scraper
        result = smart_scraper_graph.run()
        
        print("✅ ScrapeGraph AI completed successfully!")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ ScrapeGraph AI failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Testing ScrapeGraph AI for Yellow Pages scraping...")
    print("=" * 60)
    
    result = test_scrapegraph_yellowpages()
    
    if result:
        print("\n" + "=" * 60)
        print("SUCCESS - ScrapeGraph AI extracted data:")
        print(result)
    else:
        print("\n" + "=" * 60)
        print("FAILED - Could not extract data")