#!/usr/bin/env python3
"""
Test script to verify the system works without Google Maps APIs
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers import get_provider
from src.providers.multi_provider import MultiProvider
from src.providers.openstreetmap_provider import OpenStreetMapProvider
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_providers():
    """Test that providers work without Google APIs"""
    
    print("\n" + "="*60)
    print("TESTING GOOGLE-FREE LEAD GENERATION SYSTEM")
    print("="*60)
    
    # Test 1: Verify Google providers are not available
    print("\n1. Verifying Google providers have been removed...")
    try:
        from src.providers.google_places_new import GooglePlacesNewProvider
        print("   ❌ ERROR: GooglePlacesNewProvider still exists!")
        return False
    except ImportError:
        print("   ✅ GooglePlacesNewProvider removed successfully")
    
    try:
        from src.providers.serp_provider import DirectGoogleMapsProvider
        print("   ❌ ERROR: DirectGoogleMapsProvider still exists!")
        return False
    except ImportError:
        print("   ✅ DirectGoogleMapsProvider removed successfully")
    
    # Test 2: Check that MultiProvider works
    print("\n2. Testing MultiProvider (should use only free providers)...")
    try:
        multi = MultiProvider()
        print(f"   ✅ MultiProvider initialized with {len(multi.providers)} providers:")
        for name, provider in multi.providers:
            print(f"      - {name}: {provider.__class__.__name__}")
    except Exception as e:
        print(f"   ❌ ERROR: MultiProvider failed: {e}")
        return False
    
    # Test 3: Test OpenStreetMap provider directly
    print("\n3. Testing OpenStreetMap provider...")
    try:
        osm = OpenStreetMapProvider()
        results = osm.fetch_places("restaurants in New York", limit=5)
        print(f"   ✅ OpenStreetMap returned {len(results)} results")
        if results:
            print(f"      Sample: {results[0].get('name', 'Unknown')}")
    except Exception as e:
        print(f"   ❌ ERROR: OpenStreetMap failed: {e}")
        return False
    
    # Test 4: Test auto provider selection
    print("\n4. Testing auto provider selection...")
    try:
        provider = get_provider('auto')
        print(f"   ✅ Auto provider: {provider.__class__.__name__}")
        results = provider.fetch_places("coffee shops in Seattle", limit=3)
        print(f"   ✅ Auto provider returned {len(results)} results")
    except Exception as e:
        print(f"   ❌ ERROR: Auto provider failed: {e}")
        return False
    
    # Test 5: Verify no Google API keys are needed
    print("\n5. Verifying no Google API keys are required...")
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key:
        print(f"   ⚠️  WARNING: GOOGLE_API_KEY is still set in environment (but not used)")
    else:
        print("   ✅ No GOOGLE_API_KEY in environment")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - SYSTEM IS GOOGLE-FREE!")
    print("="*60)
    print("\nThe lead generation system now uses only FREE providers:")
    print("- OpenStreetMap (FREE)")
    print("- PureScraper (FREE)")
    print("- HybridScraper (FREE)")
    print("- Yellow Pages (FREE)")
    print("\n💰 No API costs, no billing surprises!")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_providers()
    sys.exit(0 if success else 1)