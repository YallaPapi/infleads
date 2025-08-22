#!/usr/bin/env python3
"""Verify lead generation is working after fixes"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:5001"

print("\nVERIFYING LEAD GENERATION FIXES")
print("-"*50)

# Submit a test job
payload = {
    "query": "restaurants in Manhattan New York", 
    "limit": 5
}

print(f"Testing: {payload['query']}")
print(f"Limit: {payload['limit']}")

try:
    # Submit the job
    response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=10)
    
    if response.status_code != 200:
        print(f"FAILED: Job submission returned {response.status_code}")
        sys.exit(1)
    
    job_data = response.json()
    job_id = job_data.get('job_id')
    print(f"Job ID: {job_id}")
    
    # Wait and check status
    print("\nWaiting for results...")
    
    max_checks = 15
    for check in range(max_checks):
        time.sleep(2)
        
        status_response = requests.get(f"{BASE_URL}/api/status/{job_id}", timeout=5)
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get('status')
            progress = status_data.get('progress', 0) 
            
            print(f"  Check {check+1}: status={status}, progress={progress}%")
            
            if status == 'completed':
                results = status_data.get('results', [])
                
                print("\n" + "="*50)
                print(f"RESULTS: Found {len(results)} leads")
                print("="*50)
                
                if len(results) > 0:
                    print("\nSUCCESS - Lead generation is working!")
                    print("\nSample leads found:")
                    
                    for i, lead in enumerate(results[:5], 1):
                        print(f"\n{i}. {lead.get('name', 'Unknown')}")
                        print(f"   Address: {lead.get('address', 'N/A')}")
                        print(f"   Source: {lead.get('source', 'N/A')}")
                        if lead.get('phone'):
                            print(f"   Phone: {lead.get('phone')}")
                        if lead.get('website'):
                            print(f"   Website: {lead.get('website')}")
                    
                    print("\n" + "="*50)
                    print("LEAD GENERATION IS WORKING!")
                    print("="*50)
                else:
                    print("\nFAILED - No leads returned")
                    print("The system is still not working properly")
                
                break
                
            elif status == 'failed':
                error = status_data.get('error', 'Unknown error')
                print(f"\nFAILED: Job failed with error: {error}")
                break
    
    else:
        print("\nTIMEOUT: Job did not complete in 30 seconds")
        
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)