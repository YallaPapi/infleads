#!/usr/bin/env python3
"""
Test with full logging to see exactly what's happening with Instantly
"""

import requests
import time
import json

BASE_URL = "http://localhost:5000"
TEST_CAMPAIGN_ID = "3fe86e51-baed-4fda-9b81-c6f8c2b93063"  # 'test' campaign

print("Starting test with full logging...")

# Small test with verified emails
request_data = {
    'query': 'restaurants in Miami',
    'limit': 3,
    'verify_emails': True,
    'generate_emails': False,  # Skip to save time
    'providers': ['google_maps'],
    'add_to_instantly': True,
    'instantly_campaign': TEST_CAMPAIGN_ID
}

print(f"Query: {request_data['query']}")
print(f"Campaign: {TEST_CAMPAIGN_ID}")

response = requests.post(f"{BASE_URL}/api/generate", json=request_data)

if response.status_code != 200:
    print(f"Failed to start job: {response.text}")
    exit(1)

job_id = response.json().get('job_id')
print(f"Job started: {job_id}")

# Monitor progress
print("\nMonitoring progress...")
for i in range(60):
    response = requests.get(f"{BASE_URL}/api/status/{job_id}")
    
    if response.status_code == 200:
        data = response.json()
        status = data.get('status')
        message = data.get('message', '')
        
        print(f"[{i:2}] {status:20} | {message}")
        
        if status == 'completed':
            print(f"\n{'='*60}")
            print("FINAL MESSAGE:", message)
            print(f"{'='*60}")
            break
            
        elif status == 'error':
            print(f"Job failed: {data.get('error')}")
            break
    
    time.sleep(2)

print("\n[CHECK SERVER CONSOLE FOR DETAILED INSTANTLY API LOGS]")