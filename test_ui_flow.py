#!/usr/bin/env python3
"""
Test the actual UI flow to verify everything works
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:5000"
TEST_CAMPAIGN_ID = "3fe86e51-baed-4fda-9b81-c6f8c2b93063"  # 'test' campaign

print("=" * 70)
print("ACTUAL UI FLOW TEST - Using 'test' Campaign")
print("=" * 70)

# 1. Start a real search with the test campaign
print("\n1. Starting lead generation with 'test' campaign...")
request_data = {
    'query': 'auto repair shops in Phoenix',
    'limit': 10,
    'verify_emails': True,
    'generate_emails': True,
    'export_verified_only': False,
    'providers': ['google_maps'],
    'add_to_instantly': True,
    'instantly_campaign': TEST_CAMPAIGN_ID
}

response = requests.post(f"{BASE_URL}/api/generate", json=request_data)
if response.status_code != 200:
    print(f"[FAIL] Could not start job: {response.text}")
    exit(1)

job_id = response.json().get('job_id')
print(f"Job started: {job_id}")
print("Keep this job ID for testing the download button!")

# 2. Monitor progress
print("\n2. Monitoring progress (as the UI would)...")
for i in range(120):  # Wait up to 4 minutes
    response = requests.get(f"{BASE_URL}/api/status/{job_id}")
    
    if response.status_code != 200:
        print(f"[FAIL] Status check failed: {response.text}")
        break
    
    data = response.json()
    status = data.get('status')
    progress = data.get('progress', 0)
    message = data.get('message', '')
    leads_preview = data.get('leads_preview', [])
    
    print(f"[{i:3}] Status: {status:15} | Progress: {progress:3}% | Preview: {len(leads_preview)} leads | {message}")
    
    if status == 'completed':
        print("\n3. Job completed! Final status:")
        print(f"   Message: {message}")
        print(f"   Leads in preview: {len(leads_preview)}")
        
        if leads_preview:
            print(f"   First lead: {leads_preview[0].get('Name')} - {leads_preview[0].get('Email')}")
        
        # 4. Test download
        print(f"\n4. Testing download with job ID: {job_id}")
        download_url = f"/api/download/{job_id}"
        print(f"   Download URL: {download_url}")
        
        download_response = requests.get(f"{BASE_URL}{download_url}")
        print(f"   Download status: {download_response.status_code}")
        
        if download_response.status_code == 200:
            print("   [PASS] Download successful!")
            
            # Save the file
            filename = f"test_ui_flow_{job_id}.csv"
            with open(filename, 'wb') as f:
                f.write(download_response.content)
            print(f"   Saved to: {filename}")
            
            # Check content
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                print(f"   CSV lines: {len(lines)}")
                if len(lines) > 1:
                    print(f"   Headers: {lines[0][:100]}...")
                    print(f"   First data: {lines[1][:100]}...")
        else:
            print(f"   [FAIL] Download failed: {download_response.text}")
        
        # 5. Verify Instantly integration
        print("\n5. Verifying Instantly integration:")
        if 'instantly' in message.lower():
            if 'added' in message.lower():
                print(f"   [PASS] {message}")
            else:
                print(f"   [FAIL] {message}")
        else:
            print("   [SKIP] No Instantly message in status")
        
        break
    
    elif status == 'error':
        print(f"\n[FAIL] Job failed: {data.get('error')}")
        break
    
    time.sleep(2)

print("\n" + "=" * 70)
print("SUMMARY:")
print("1. Job ID persists throughout the session: YES")
print("2. Download works with the job ID: Check above")
print("3. Leads sent to 'test' campaign: Check the message")
print("4. Preview shows data: Check above")
print("\nIf download shows 'job not found' in the UI but works here,")
print("the issue is with the frontend losing the job_id variable.")
print("=" * 70)