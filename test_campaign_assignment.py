#!/usr/bin/env python3
"""
Test different ways to assign a lead to a campaign
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('INSTANTLY_API_KEY')
BASE_URL = "https://api.instantly.ai/api/v2"
TEST_CAMPAIGN_ID = "3fe86e51-baed-4fda-9b81-c6f8c2b93063"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

print("=" * 70)
print("TESTING CAMPAIGN ASSIGNMENT METHODS")
print("=" * 70)

# Method 1: Try campaign_id field
test_lead_1 = {
    "email": f"method1_{int(time.time())}@example.com",
    "first_name": "Method1",
    "campaign_id": TEST_CAMPAIGN_ID
}

print("\nMethod 1: Using 'campaign_id' field")
print(f"Email: {test_lead_1['email']}")

response = requests.post(f"{BASE_URL}/leads", headers=headers, json=test_lead_1)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Created: {data.get('id')}")
    print(f"Has campaign_id in response? {'campaign_id' in data}")

# Method 2: Try campaign field
test_lead_2 = {
    "email": f"method2_{int(time.time())}@example.com",
    "first_name": "Method2",
    "campaign": TEST_CAMPAIGN_ID
}

print("\nMethod 2: Using 'campaign' field")
print(f"Email: {test_lead_2['email']}")

response = requests.post(f"{BASE_URL}/leads", headers=headers, json=test_lead_2)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Created: {data.get('id')}")
    print(f"Has campaign in response? {'campaign' in data}")

# Method 3: Try campaigns array
test_lead_3 = {
    "email": f"method3_{int(time.time())}@example.com",
    "first_name": "Method3",
    "campaigns": [TEST_CAMPAIGN_ID]
}

print("\nMethod 3: Using 'campaigns' array")
print(f"Email: {test_lead_3['email']}")

response = requests.post(f"{BASE_URL}/leads", headers=headers, json=test_lead_3)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Created: {data.get('id')}")
    print(f"Has campaigns in response? {'campaigns' in data}")

# Method 4: Try to add to campaign after creation
print("\nMethod 4: Create lead first, then add to campaign")
test_lead_4 = {
    "email": f"method4_{int(time.time())}@example.com",
    "first_name": "Method4"
}

response = requests.post(f"{BASE_URL}/leads", headers=headers, json=test_lead_4)
if response.status_code == 200:
    lead_data = response.json()
    lead_id = lead_data.get('id')
    print(f"Created lead: {lead_id}")
    
    # Now try to add to campaign
    print("Trying to add to campaign...")
    
    # Try different endpoints
    endpoints = [
        f"campaigns/{TEST_CAMPAIGN_ID}/leads/{lead_id}",
        f"leads/{lead_id}/campaigns/{TEST_CAMPAIGN_ID}",
        f"campaigns/{TEST_CAMPAIGN_ID}/add-lead"
    ]
    
    for endpoint in endpoints:
        print(f"  Trying: {endpoint}")
        response = requests.post(f"{BASE_URL}/{endpoint}", headers=headers)
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            print(f"    SUCCESS!")
            break

print("\n" + "=" * 70)
print("CONCLUSION:")
print("Check which method (if any) successfully adds leads to the campaign.")
print("The issue is that leads are being created but NOT assigned to campaigns!")
print("=" * 70)