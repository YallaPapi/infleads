#!/usr/bin/env python3
"""
Test with the CORRECT campaign ID
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('INSTANTLY_API_KEY')
BASE_URL = "https://api.instantly.ai/api/v2"

# THE CORRECT TEST CAMPAIGN ID!
TEST_CAMPAIGN_ID = "6d613d64-51b8-44ab-8f6d-985dab212307"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

print("=" * 70)
print("TESTING WITH CORRECT CAMPAIGN ID")
print("=" * 70)
print(f"Campaign: test")
print(f"ID: {TEST_CAMPAIGN_ID}")
print("=" * 70)

# Test 1: Try campaign_ids array (worked in previous test)
test_email1 = f"correct_test1_{int(time.time())}@example.com"
lead_data1 = {
    "email": test_email1,
    "first_name": "Correct",
    "last_name": "Test1",
    "company_name": "Test Company",
    "campaign_ids": [TEST_CAMPAIGN_ID]
}

print(f"\n1. Testing 'campaign_ids' array method:")
print(f"   Email: {test_email1}")

response = requests.post(f"{BASE_URL}/leads", headers=headers, json=lead_data1)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"   SUCCESS! Lead created with ID: {data.get('id')}")
    print(f"   Check if 'campaign_ids' in response: {'campaign_ids' in data}")
    if 'campaign_ids' in data:
        print(f"   Campaign IDs: {data.get('campaign_ids')}")
else:
    print(f"   Failed: {response.text[:200]}")

# Test 2: Try campaign field with correct ID
test_email2 = f"correct_test2_{int(time.time())}@example.com"
lead_data2 = {
    "email": test_email2,
    "first_name": "Correct",
    "last_name": "Test2",
    "company_name": "Test Company",
    "campaign": TEST_CAMPAIGN_ID
}

print(f"\n2. Testing 'campaign' field method:")
print(f"   Email: {test_email2}")

response = requests.post(f"{BASE_URL}/leads", headers=headers, json=lead_data2)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"   SUCCESS! Lead created with ID: {data.get('id')}")
    print(f"   Check if 'campaign' in response: {'campaign' in data}")
else:
    print(f"   Failed: {response.text[:200]}")

# Test 3: Try the move endpoint with correct campaign ID
test_email3 = f"correct_test3_{int(time.time())}@example.com"
lead_data3 = {
    "email": test_email3,
    "first_name": "Correct",
    "last_name": "Test3",
    "company_name": "Test Company"
}

print(f"\n3. Testing two-step process (create then move):")
print(f"   Email: {test_email3}")

response = requests.post(f"{BASE_URL}/leads", headers=headers, json=lead_data3)
if response.status_code == 200:
    lead_id = response.json().get('id')
    print(f"   Lead created with ID: {lead_id}")
    
    # Now move it
    move_payload = {
        "ids": [lead_id],
        "to_campaign_id": TEST_CAMPAIGN_ID,
        "check_duplicates_in_campaigns": True,
        "copy_leads": False
    }
    
    print(f"   Moving to campaign...")
    response = requests.post(f"{BASE_URL}/leads/move", headers=headers, json=move_payload)
    print(f"   Move status: {response.status_code}")
    
    if response.status_code == 200:
        move_data = response.json()
        print(f"   Move job status: {move_data.get('status')}")
        print(f"   Job ID: {move_data.get('id')}")
        print("   (Note: This is async - check Instantly in a few seconds)")
else:
    print(f"   Failed to create: {response.text[:200]}")

print("\n" + "=" * 70)
print("RESULTS:")
print("1. Check your Instantly 'test' campaign NOW")
print("2. You should see these test leads appearing")
print("3. The correct campaign ID is being used!")
print("=" * 70)