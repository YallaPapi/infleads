#!/usr/bin/env python3
"""
Direct test of Instantly API to verify it works
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('INSTANTLY_API_KEY')
TEST_CAMPAIGN_ID = "3fe86e51-baed-4fda-9b81-c6f8c2b93063"

# Test adding a lead directly to Instantly
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Single lead test
lead = {
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "company_name": "Test Company",
    "campaign_id": TEST_CAMPAIGN_ID
}

print("Testing single lead addition...")
response = requests.post(
    "https://api.instantly.ai/api/v2/leads",
    headers=headers,
    json=lead  # Single lead, not array
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Now test with array format
print("\nTesting array format...")
payload = {
    "leads": [{
        "email": "test2@example.com",
        "first_name": "Test2",
        "last_name": "User2",
        "company_name": "Test Company 2",
        "campaign_id": TEST_CAMPAIGN_ID
    }]
}

response = requests.post(
    "https://api.instantly.ai/api/v2/leads",
    headers=headers,
    json=payload
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Test without campaign_id
print("\nTesting without campaign_id...")
payload = {
    "leads": [{
        "email": "test3@example.com",
        "first_name": "Test3",
        "last_name": "User3",
        "company_name": "Test Company 3"
    }]
}

response = requests.post(
    "https://api.instantly.ai/api/v2/leads",
    headers=headers,
    json=payload
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")