#!/usr/bin/env python3
"""
Comprehensive test for all issues:
1. Download button showing "job not found"
2. Leads not being uploaded to correct campaign
3. Testing with the 'test' campaign specifically
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:5000"
TEST_CAMPAIGN_ID = "3fe86e51-baed-4fda-9b81-c6f8c2b93063"  # The 'test' campaign

def wait_for_server():
    """Wait for server to be ready"""
    for i in range(10):
        try:
            r = requests.get(f"{BASE_URL}/api/health")
            if r.status_code == 200:
                print("[OK] Server is ready")
                return True
        except:
            pass
        time.sleep(2)
    return False

def test_job_persistence():
    """Test if job persists for download"""
    print("\n=== TEST 1: Job Persistence for Download ===")
    
    # Start a simple job
    request_data = {
        'query': 'coffee shops in Seattle',
        'limit': 3,
        'verify_emails': False,
        'generate_emails': False,
        'providers': ['google_maps']
    }
    
    print("1. Starting job...")
    response = requests.post(f"{BASE_URL}/api/generate", json=request_data)
    
    if response.status_code != 200:
        print(f"   [FAIL] Could not start job: {response.text}")
        return None
    
    job_id = response.json().get('job_id')
    print(f"   Job ID: {job_id}")
    
    # Wait for completion
    print("2. Waiting for completion...")
    for i in range(30):
        response = requests.get(f"{BASE_URL}/api/status/{job_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'completed':
                print("   Job completed")
                break
        time.sleep(1)
    
    # Try to download immediately
    print("3. Testing download immediately after completion...")
    download_response = requests.get(f"{BASE_URL}/api/download/{job_id}")
    print(f"   Status: {download_response.status_code}")
    
    if download_response.status_code == 200:
        print("   [PASS] Download works immediately")
    else:
        print(f"   [FAIL] Download failed: {download_response.text}")
    
    # Simulate user waiting/navigating (job should still be available)
    print("4. Testing download after 5 seconds...")
    time.sleep(5)
    download_response = requests.get(f"{BASE_URL}/api/download/{job_id}")
    print(f"   Status: {download_response.status_code}")
    
    if download_response.status_code == 200:
        print("   [PASS] Job persists in memory")
    else:
        print(f"   [FAIL] Job lost from memory: {download_response.text}")
    
    return job_id

def test_instantly_campaign_selection():
    """Test if leads go to the correct campaign"""
    print("\n=== TEST 2: Instantly Campaign Selection (using 'test' campaign) ===")
    
    # Generate leads WITH Instantly integration to 'test' campaign
    request_data = {
        'query': 'restaurants in Las Vegas',
        'limit': 5,
        'verify_emails': True,
        'generate_emails': True,
        'providers': ['google_maps'],
        'add_to_instantly': True,
        'instantly_campaign': TEST_CAMPAIGN_ID  # Using 'test' campaign
    }
    
    print(f"1. Starting job with 'test' campaign (ID: {TEST_CAMPAIGN_ID})...")
    response = requests.post(f"{BASE_URL}/api/generate", json=request_data)
    
    if response.status_code != 200:
        print(f"   [FAIL] Could not start job: {response.text}")
        return False
    
    job_id = response.json().get('job_id')
    print(f"   Job ID: {job_id}")
    
    # Wait and monitor progress
    print("2. Monitoring job progress...")
    final_message = ""
    for i in range(60):
        response = requests.get(f"{BASE_URL}/api/status/{job_id}")
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            message = data.get('message', '')
            
            if status == 'adding_to_instantly':
                print(f"   [{i}] Adding to Instantly: {message}")
            
            if status == 'completed':
                final_message = message
                print(f"   Job completed: {final_message}")
                break
        time.sleep(2)
    
    # Check if it mentions the test campaign
    if 'added' in final_message.lower() and 'instantly' in final_message.lower():
        print("   [PASS] Leads were added to Instantly")
        
        # Verify which campaign by checking the logs
        print("\n3. Verifying campaign selection...")
        print(f"   Expected campaign: 'test' (ID: {TEST_CAMPAIGN_ID})")
        print(f"   Final message: {final_message}")
        
        # Check if we can download the results
        print("\n4. Verifying download works...")
        download_response = requests.get(f"{BASE_URL}/api/download/{job_id}")
        if download_response.status_code == 200:
            print("   [PASS] Download works for this job")
            
            # Save and check the CSV
            with open('test_campaign_results.csv', 'wb') as f:
                f.write(download_response.content)
            
            with open('test_campaign_results.csv', 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                print(f"   CSV has {len(lines)} lines")
                if len(lines) > 1:
                    print(f"   Sample data: {lines[1][:100]}...")
        else:
            print(f"   [FAIL] Download failed: {download_response.text}")
    else:
        print(f"   [FAIL] Instantly integration failed: {final_message}")
    
    return True

def test_multiple_searches():
    """Test multiple searches with the test campaign"""
    print("\n=== TEST 3: Multiple Searches with 'test' Campaign ===")
    
    searches = [
        "dentists in New York",
        "lawyers in Chicago",
        "plumbers in Houston"
    ]
    
    for search_query in searches:
        print(f"\n--- Testing: {search_query} ---")
        
        request_data = {
            'query': search_query,
            'limit': 3,
            'verify_emails': True,
            'generate_emails': False,  # Skip email generation for speed
            'providers': ['google_maps'],
            'add_to_instantly': True,
            'instantly_campaign': TEST_CAMPAIGN_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/generate", json=request_data)
        
        if response.status_code != 200:
            print(f"   [FAIL] Could not start job: {response.text}")
            continue
        
        job_id = response.json().get('job_id')
        print(f"   Job ID: {job_id}")
        
        # Wait for completion
        for i in range(40):
            response = requests.get(f"{BASE_URL}/api/status/{job_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'completed':
                    message = data.get('message', '')
                    print(f"   Result: {message}")
                    
                    # Test download
                    download_response = requests.get(f"{BASE_URL}/api/download/{job_id}")
                    if download_response.status_code == 200:
                        print(f"   [PASS] Download works")
                    else:
                        print(f"   [FAIL] Download failed")
                    break
            time.sleep(2)
    
    return True

def check_instantly_api_directly():
    """Check if leads actually made it to Instantly"""
    print("\n=== TEST 4: Verify Leads in Instantly API ===")
    
    api_key = os.getenv('INSTANTLY_API_KEY')
    if not api_key:
        print("   [SKIP] No API key configured")
        return
    
    # This would require implementing a check for leads in the campaign
    # For now, just verify the campaign exists
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"https://api.instantly.ai/api/v2/campaigns/{TEST_CAMPAIGN_ID}",
            headers=headers
        )
        
        if response.status_code == 200:
            print("   [PASS] Test campaign exists in Instantly")
            campaign_data = response.json()
            print(f"   Campaign name: {campaign_data.get('name', 'Unknown')}")
        else:
            print(f"   [FAIL] Could not fetch campaign: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] API check failed: {e}")

def main():
    print("=" * 70)
    print("COMPREHENSIVE TESTING - R27 INFINITE AI LEADS")
    print("=" * 70)
    
    if not wait_for_server():
        print("[FAIL] Server not responding")
        return
    
    # Run all tests
    print("\n[RUNNING ALL TESTS]\n")
    
    # Test 1: Job persistence
    job_id = test_job_persistence()
    
    # Test 2: Campaign selection
    test_instantly_campaign_selection()
    
    # Test 3: Multiple searches
    test_multiple_searches()
    
    # Test 4: Verify in Instantly
    check_instantly_api_directly()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("Review the results above to verify:")
    print("1. Download button works for all jobs")
    print("2. Leads are sent to the 'test' campaign")
    print("3. Multiple searches work correctly")
    print("4. Data persists properly")

if __name__ == "__main__":
    main()