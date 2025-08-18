#!/usr/bin/env python3
"""
Test the /api/v2/leads/move endpoint directly to see what it actually returns
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
print("TESTING LEAD MOVE ENDPOINT DIRECTLY")
print("=" * 70)

# Step 1: Create a test lead WITHOUT campaign
test_email = f"move_test_{int(time.time())}@example.com"
lead_data = {
    "email": test_email,
    "first_name": "Move",
    "last_name": "Test",
    "company_name": "Test Company"
}

print(f"\n1. Creating lead: {test_email}")
response = requests.post(f"{BASE_URL}/leads", headers=headers, json=lead_data)

if response.status_code != 200:
    print(f"Failed to create lead: {response.status_code}")
    print(response.text)
    exit(1)

lead_response = response.json()
lead_id = lead_response.get('id')
print(f"   Created with ID: {lead_id}")

# Step 2: Try to move the lead to campaign
print(f"\n2. Moving lead to campaign: {TEST_CAMPAIGN_ID}")

move_payload = {
    "ids": [lead_id],
    "to_campaign_id": TEST_CAMPAIGN_ID,
    "check_duplicates_in_campaigns": True,
    "copy_leads": False
}

print("   Request payload:")
print(json.dumps(move_payload, indent=4))

response = requests.post(f"{BASE_URL}/leads/move", headers=headers, json=move_payload)

print(f"\n3. Move Response:")
print(f"   Status: {response.status_code}")
print(f"   Headers: {dict(response.headers)}")
print(f"   Body: {response.text}")

if response.status_code == 200:
    try:
        data = response.json()
        print("\n   Parsed Response:")
        print(json.dumps(data, indent=4))
    except:
        print("   (Empty or non-JSON response)")

# Step 3: Try alternative endpoints
print("\n4. Testing alternative endpoints:")

# Try with campaign field during creation
test_email2 = f"campaign_test_{int(time.time())}@example.com"
lead_data2 = {
    "email": test_email2,
    "first_name": "Campaign",
    "last_name": "Test",
    "company_name": "Test Company",
    "campaign": TEST_CAMPAIGN_ID  # Try with campaign field
}

print(f"\n   Creating lead with 'campaign' field: {test_email2}")
response = requests.post(f"{BASE_URL}/leads", headers=headers, json=lead_data2)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print("   SUCCESS - This might be the correct way!")
    data = response.json()
    print(f"   Lead ID: {data.get('id')}")
else:
    print(f"   Failed: {response.text[:200]}")

# Try with campaign_ids array
test_email3 = f"campaigns_test_{int(time.time())}@example.com"
lead_data3 = {
    "email": test_email3,
    "first_name": "Campaigns",
    "last_name": "Test",
    "company_name": "Test Company",
    "campaign_ids": [TEST_CAMPAIGN_ID]  # Try with campaign_ids array
}

print(f"\n   Creating lead with 'campaign_ids' array: {test_email3}")
response = requests.post(f"{BASE_URL}/leads", headers=headers, json=lead_data3)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print("   SUCCESS - This might be the correct way!")
    data = response.json()
    print(f"   Lead ID: {data.get('id')}")
else:
    print(f"   Failed: {response.text[:200]}")

print("\n" + "=" * 70)
print("CONCLUSION:")
print("Check which method actually works for assigning to campaigns")
print("The 200 OK response might be misleading us!")
print("=" * 70)