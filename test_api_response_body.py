#!/usr/bin/env python3
"""
Test what the Instantly API is ACTUALLY returning in the response body
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('INSTANTLY_API_KEY')
BASE_URL = "https://api.instantly.ai/api/v2"
TEST_CAMPAIGN_ID = "3fe86e51-baed-4fda-9b81-c6f8c2b93063"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Test lead data
test_lead = {
    "email": f"test_debug_123@example.com",
    "first_name": "Test",
    "last_name": "Debug",
    "company_name": "Test Company",
    "campaign_id": TEST_CAMPAIGN_ID
}

print("=" * 70)
print("TESTING INSTANTLY API DIRECTLY")
print("=" * 70)
print(f"\nSending test lead to campaign: {TEST_CAMPAIGN_ID}")
print(f"Lead email: {test_lead['email']}")
print("\nRequest body:")
print(json.dumps(test_lead, indent=2))

# Make the request
response = requests.post(
    f"{BASE_URL}/leads",
    headers=headers,
    json=test_lead
)

print(f"\n{'='*70}")
print("RESPONSE DETAILS:")
print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"\nResponse Body (RAW):")
print(response.text)

if response.status_code == 200:
    print("\n" + "="*70)
    print("STATUS 200 - But let's check what it actually means...")
    
    try:
        data = response.json()
        print("\nParsed JSON Response:")
        print(json.dumps(data, indent=2))
        
        # Check if there's an ID (successful creation)
        if 'id' in data:
            print(f"\n✓ Lead created with ID: {data['id']}")
            print("This SHOULD mean the lead is in Instantly!")
        elif 'error' in data:
            print(f"\n✗ Error in response: {data['error']}")
        else:
            print(f"\n? Unexpected response format - check the full response above")
            
    except Exception as e:
        print(f"\nCouldn't parse JSON: {e}")
        print("This might mean an empty or invalid response")
else:
    print(f"\n✗ Request failed with status {response.status_code}")

print("\n" + "="*70)
print("WHAT TO CHECK:")
print("1. If you see an ID above, the lead SHOULD be in Instantly")
print("2. Check if the campaign_id matches your 'test' campaign")
print("3. Look for any error messages in the response")
print("4. Check if the response is actually empty (200 but no content)")
print("=" * 70)