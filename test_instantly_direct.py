#!/usr/bin/env python3
"""
Direct test of Instantly.ai API to see what's actually happening
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_instantly_api():
    api_key = os.getenv('INSTANTLY_API_KEY')
    
    if not api_key:
        print("ERROR: No INSTANTLY_API_KEY found in environment")
        return
        
    print(f"Using API key: {api_key[:10]}..." if len(api_key) > 10 else api_key)
    
    # Test 1: Get campaigns
    print("\n" + "="*60)
    print("TEST 1: Getting campaigns")
    print("="*60)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get('https://api.instantly.ai/api/v2/campaigns', headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            campaigns_response = response.json()
            print(f"SUCCESS: API response received")
            print(f"Response structure: {json.dumps(campaigns_response, indent=2)[:500]}...")
            
            # Handle Instantly.ai API structure
            if 'items' in campaigns_response:
                campaigns = campaigns_response['items']
            else:
                campaigns = campaigns_response
            
            print(f"Found {len(campaigns)} campaigns")
            
            if campaigns:
                campaign = campaigns[0]
                campaign_id = campaign.get('id')
                print(f"First campaign ID: {campaign_id}")
                print(f"First campaign name: {campaign.get('name')}")
                print(f"Campaign status: {campaign.get('status')}")
                
                # Test 2: Create a test lead
                print("\n" + "="*60)
                print("TEST 2: Creating test lead")
                print("="*60)
                
                test_lead = {
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "Lead",
                    "company_name": "Test Company",
                    "campaign": campaign_id
                }
                
                print(f"Sending payload: {json.dumps(test_lead, indent=2)}")
                
                response = requests.post('https://api.instantly.ai/api/v2/leads', 
                                       headers=headers, 
                                       json=test_lead)
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
                if response.status_code == 200 or response.status_code == 201:
                    print("SUCCESS: Lead created successfully!")
                else:
                    print("ERROR: Lead creation failed!")
                    print(f"Error details: {response.text}")
            else:
                print("ERROR: No campaigns found")
        else:
            print(f"ERROR: Failed to get campaigns: {response.text}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == '__main__':
    test_instantly_api()
