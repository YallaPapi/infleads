#!/usr/bin/env python3
"""Quick test to verify lead generation is working"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

print("\n🔍 QUICK LEAD GENERATION TEST")
print("="*40)

# Step 1: Check API health
print("\n1. Checking API health...")
try:
    health = requests.get(f"{BASE_URL}/api/health", timeout=5)
    if health.status_code == 200:
        data = health.json()
        print(f"   ✅ API is healthy")
        print(f"   Provider: {data.get('provider', 'unknown')}")
        print(f"   OpenAI configured: {data.get('openai_configured', False)}")
    else:
        print(f"   ❌ API unhealthy: {health.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ Cannot connect to API: {e}")
    exit(1)

# Step 2: Submit a simple lead generation job
print("\n2. Submitting lead generation job...")
payload = {
    "query": "pizza restaurants",
    "location": "Manhattan, New York",
    "limit": 3,
    "provider": "auto"
}

print(f"   Query: {payload['query']}")
print(f"   Location: {payload['location']}")
print(f"   Limit: {payload['limit']}")

try:
    response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=10)
    
    if response.status_code != 200:
        print(f"   ❌ Failed to submit job: {response.status_code}")
        print(f"   Error: {response.text[:200]}")
        exit(1)
    
    job_data = response.json()
    job_id = job_data.get('job_id')
    print(f"   ✅ Job submitted: {job_id}")
    
except Exception as e:
    print(f"   ❌ Error submitting job: {e}")
    exit(1)

# Step 3: Check job status
print("\n3. Checking job status...")
for i in range(15):  # Check for 30 seconds max
    time.sleep(2)
    
    try:
        status_resp = requests.get(f"{BASE_URL}/api/status/{job_id}", timeout=5)
        
        if status_resp.status_code != 200:
            print(f"   ❌ Status check failed: {status_resp.status_code}")
            continue
            
        status_data = status_resp.json()
        status = status_data.get('status', 'unknown')
        progress = status_data.get('progress', 0)
        
        print(f"   Attempt {i+1}: Status={status}, Progress={progress}%")
        
        if status == 'completed':
            leads = status_data.get('results', [])
            print(f"\n   ✅ SUCCESS! Found {len(leads)} leads:")
            
            for idx, lead in enumerate(leads[:5], 1):
                print(f"\n   Lead {idx}:")
                print(f"     Name: {lead.get('name', 'N/A')}")
                print(f"     Address: {lead.get('address', 'N/A')}")
                print(f"     Phone: {lead.get('phone', 'N/A')}")
                if lead.get('website'):
                    print(f"     Website: {lead.get('website')}")
                if lead.get('rating'):
                    print(f"     Rating: {lead.get('rating')}")
            
            print("\n" + "="*40)
            print("✅ LEAD GENERATION IS WORKING!")
            print("="*40)
            exit(0)
            
        elif status == 'failed':
            error = status_data.get('error', 'Unknown error')
            print(f"\n   ❌ Job failed: {error}")
            
            # Try to get more details
            if 'message' in status_data:
                print(f"   Details: {status_data['message']}")
            
            exit(1)
            
    except Exception as e:
        print(f"   Error checking status: {e}")
        continue

print("\n   ⏱️ Job is taking too long (30+ seconds)")
print("   Check if providers are configured correctly")
exit(1)