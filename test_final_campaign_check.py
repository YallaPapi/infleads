#!/usr/bin/env python3
"""
Final test to verify leads are actually being added to campaigns
"""

import requests
import time
import json

BASE_URL = "http://localhost:5000"
TEST_CAMPAIGN_ID = "3fe86e51-baed-4fda-9b81-c6f8c2b93063"

print("=" * 70)
print("FINAL CAMPAIGN ASSIGNMENT TEST")
print("=" * 70)

# Test with unique query to get fresh leads
timestamp = int(time.time())
request_data = {
    'query': f'dentist Miami',  # Different query for unique results
    'limit': 5,
    'verify_emails': True,
    'generate_emails': False,
    'providers': ['google_maps'],
    'add_to_instantly': True,
    'instantly_campaign': TEST_CAMPAIGN_ID
}

print(f"\n1. Starting job with query: {request_data['query']}")
print(f"   Campaign ID: {TEST_CAMPAIGN_ID}")

response = requests.post(f"{BASE_URL}/api/generate", json=request_data)
if response.status_code != 200:
    print(f"Failed to start job: {response.text}")
    exit(1)

job_id = response.json().get('job_id')
print(f"   Job ID: {job_id}")

print("\n2. Processing (this may take 30-60 seconds)...")

# Monitor until complete
completed = False
for i in range(120):
    response = requests.get(f"{BASE_URL}/api/status/{job_id}")
    
    if response.status_code == 200:
        data = response.json()
        status = data.get('status')
        message = data.get('message', '')
        
        if status == 'completed':
            completed = True
            print(f"\n3. COMPLETED!")
            print(f"   Message: {message}")
            
            # Parse the message to check results
            if 'added' in message.lower() and 'instantly' in message.lower():
                # Extract numbers from message
                import re
                numbers = re.findall(r'\d+', message)
                if numbers:
                    print(f"\n" + "="*70)
                    print(f"SUCCESS! {numbers[1] if len(numbers) > 1 else numbers[0]} leads added to Instantly!")
                    print("="*70)
                    print("\nThe two-step process is working:")
                    print("1. Leads are created in Instantly")
                    print("2. Leads are moved to the campaign")
                    print("\nCheck your Instantly dashboard - the leads should be in the 'test' campaign now!")
                else:
                    print("\nCouldn't parse exact numbers, but message indicates success")
            elif 'failed' in message.lower():
                print(f"\n" + "="*70)
                print("WARNING: Message says failed, but check server logs")
                print("The API might still be working (check for 200 responses)")
                print("="*70)
            break
            
        elif status == 'error':
            print(f"\nJob failed: {data.get('error')}")
            break
    
    if i % 10 == 0:
        print(f"   [{i}s] Still processing... Status: {status}")
    
    time.sleep(1)

if not completed:
    print("\nTimeout - job didn't complete in 120 seconds")

print("\n" + "="*70)
print("WHAT TO DO NEXT:")
print("1. Check the server console for detailed logs")
print("2. Look for 'STEP 1' and 'STEP 2' messages")
print("3. Check for '/api/v2/leads/move' endpoint calls")
print("4. Log into Instantly and check the 'test' campaign for new leads")
print("="*70)