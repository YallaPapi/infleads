#!/usr/bin/env python3
"""
Debug provider selection in Flask context
"""

# Load environment variables exactly like Flask app does
from dotenv import load_dotenv
load_dotenv()

from src.providers import get_provider
import os

print("DEBUGGING PROVIDER SELECTION")
print("="*50)
print(f"GOOGLE_API_KEY exists: {bool(os.getenv('GOOGLE_API_KEY'))}")
print(f"APIFY_API_KEY exists: {bool(os.getenv('APIFY_API_KEY'))}")

# Test provider selection
try:
    print("\nTesting get_provider('auto')...")
    provider = get_provider('auto')
    print(f"Selected provider: {provider.__class__.__name__}")
    print(f"Provider module: {provider.__class__.__module__}")
    
    # Check if it has api_key attribute  
    if hasattr(provider, 'api_key'):
        print(f"Has api_key: {bool(provider.api_key)}")
        if provider.api_key:
            print(f"API key preview: {str(provider.api_key)[:20]}...")
    else:
        print("No api_key attribute")
        
    # Test a quick fetch to see what happens
    print("\nTesting quick fetch...")
    results = provider.fetch_places("test coffee shop", 1)
    print(f"Results count: {len(results) if results else 0}")
    
    if results and len(results) > 0:
        print("Sample result keys:", list(results[0].keys()))
        print("Sample result values:")
        for k, v in results[0].items():
            print(f"  {k}: {str(v)[:50]}...")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
