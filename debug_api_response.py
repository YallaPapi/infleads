#!/usr/bin/env python3
"""
Debug API response directly
"""

import requests
import json
import time

base_url = "http://localhost:5000"

print("TESTING API RESPONSE DIRECTLY")
print("="*50)

# Start a job
payload = {
    "query": "coffee shop miami", 
    "limit": 1,
    "verify_emails": False
}

print("1. Starting job...")
response = requests.post(f"{base_url}/api/generate", json=payload)
if response.status_code != 200:
    print(f"❌ Failed to start job: {response.status_code}")
    exit(1)

data = response.json()
job_id = data.get("job_id")
print(f"✅ Job started: {job_id}")

# Poll for completion
print("2. Polling for completion...")
for i in range(30):
    response = requests.get(f"{base_url}/api/status/{job_id}")
    if response.status_code != 200:
        print(f"❌ Status check failed: {response.status_code}")
        break
        
    data = response.json()
    status = data.get("status")
    print(f"   Status: {status}")
    
    if status == "completed":
        print("\n3. ANALYZING RESPONSE DATA:")
        print(f"   Keys in response: {list(data.keys())}")
        
        leads_preview = data.get("leads_preview", [])
        print(f"   leads_preview type: {type(leads_preview)}")
        print(f"   leads_preview length: {len(leads_preview)}")
        
        if leads_preview:
            first_lead = leads_preview[0]
            print(f"   First lead type: {type(first_lead)}")
            print(f"   First lead keys: {list(first_lead.keys())}")
            print("   First lead values:")
            for k, v in first_lead.items():
                print(f"     {k}: {repr(v)}")
        break
    elif status == "error":
        print(f"❌ Job failed: {data.get('error')}")
        break
    
    time.sleep(1)
