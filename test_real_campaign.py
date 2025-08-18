#!/usr/bin/env python3
"""
Test with the REAL test campaign ID: 6d613d64-51b8-44ab-8f6d-985dab212307
"""

import requests
import time

BASE_URL = "http://localhost:5000"

# THE CORRECT TEST CAMPAIGN ID!
TEST_CAMPAIGN_ID = "6d613d64-51b8-44ab-8f6d-985dab212307"

print("=" * 70)
print("FINAL TEST WITH CORRECT CAMPAIGN ID")
print("=" * 70)
print(f"Campaign: test")
print(f"ID: {TEST_CAMPAIGN_ID}")
print("=" * 70)

request_data = {
    'query': 'lawyers in Boston',  # Fresh query
    'limit': 3,
    'verify_emails': False,  # Skip for speed
    'generate_emails': False,
    'providers': ['google_maps'],
    'add_to_instantly': True,
    'instantly_campaign': TEST_CAMPAIGN_ID  # CORRECT ID!
}

print(f"\n1. Starting job with CORRECT campaign ID")
print(f"   Query: {request_data['query']}")

response = requests.post(f"{BASE_URL}/api/generate", json=request_data)
if response.status_code != 200:
    print(f"Failed to start: {response.text}")
    exit(1)

job_id = response.json().get('job_id')
print(f"   Job ID: {job_id}")

print("\n2. Processing...")

# Monitor
for i in range(60):
    response = requests.get(f"{BASE_URL}/api/status/{job_id}")
    
    if response.status_code == 200:
        data = response.json()
        status = data.get('status')
        message = data.get('message', '')
        
        if status == 'completed':
            print(f"\n3. COMPLETED!")
            print(f"   {message}")
            
            print("\n" + "="*70)
            print("NOW CHECK YOUR INSTANTLY DASHBOARD!")
            print("Go to the 'test' campaign and verify the leads are there!")
            print("They should include lawyers from Boston")
            print("="*70)
            break
            
        elif status == 'error':
            print(f"\nFailed: {data.get('error')}")
            break
    
    if i % 5 == 0:
        print(f"   [{i}s] {status}...")
    
    time.sleep(1)