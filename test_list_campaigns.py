#!/usr/bin/env python3
"""
List all campaigns to verify the test campaign ID is correct
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('INSTANTLY_API_KEY')
BASE_URL = "https://api.instantly.ai/api/v2"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

print("=" * 70)
print("LISTING ALL INSTANTLY CAMPAIGNS")
print("=" * 70)

# Get all campaigns
response = requests.get(f"{BASE_URL}/campaigns", headers=headers)

print(f"\nStatus: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    # Handle different response formats
    if isinstance(data, list):
        campaigns = data
    elif isinstance(data, dict):
        campaigns = data.get('data', data.get('items', data.get('campaigns', [])))
    else:
        campaigns = []
    
    print(f"Found {len(campaigns)} campaigns:\n")
    
    test_campaign_found = False
    for campaign in campaigns:
        campaign_id = campaign.get('id', campaign.get('campaign_id', 'Unknown'))
        campaign_name = campaign.get('name', campaign.get('campaign_name', 'Unknown'))
        status = campaign.get('status', 'Unknown')
        
        print(f"Campaign: {campaign_name}")
        print(f"  ID: {campaign_id}")
        print(f"  Status: {status}")
        
        # Check if this is the test campaign
        if campaign_name.lower() == 'test' or campaign_id == '3fe86e51-baed-4fda-9b81-c6f8c2b93063':
            print(f"  >>> THIS IS THE TEST CAMPAIGN <<<")
            test_campaign_found = True
            
        print()
    
    if not test_campaign_found:
        print("!" * 70)
        print("WARNING: The 'test' campaign with ID 3fe86e51-baed-4fda-9b81-c6f8c2b93063")
        print("was NOT found in your Instantly account!")
        print("This is why leads aren't being added to it!")
        print("!" * 70)
else:
    print(f"Failed to get campaigns: {response.text}")

print("\n" + "=" * 70)
print("IMPORTANT:")
print("If the test campaign isn't listed above, that's the problem!")
print("The campaign ID we're using doesn't exist in your account.")
print("=" * 70)