#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. Instantly API integration
2. Download button functionality  
3. Lead preview display
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:5000"

def test_instantly_api():
    """Test Instantly API integration"""
    print("\n=== Testing Instantly API Integration ===")
    
    # Check if API key is configured
    api_key = os.getenv('INSTANTLY_API_KEY')
    if not api_key:
        print("[FAIL] INSTANTLY_API_KEY not found in environment")
        return False
    
    print(f"[OK] API Key found: {api_key[:10]}...")
    
    # Test API status endpoint
    print("\nTesting /api/instantly/status...")
    response = requests.get(f"{BASE_URL}/api/instantly/status")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        if data.get('success'):
            print("[OK] Instantly API connection successful")
        else:
            print("[FAIL] Instantly API connection failed")
            return False
    else:
        print(f"[FAIL] Status check failed: {response.text}")
        return False
    
    # Test campaigns endpoint
    print("\nTesting /api/instantly/campaigns...")
    response = requests.get(f"{BASE_URL}/api/instantly/campaigns")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        campaigns = response.json()
        print(f"Campaigns found: {len(campaigns) if isinstance(campaigns, list) else 'Invalid response'}")
        if isinstance(campaigns, list):
            print("[OK] Campaigns endpoint working")
            for campaign in campaigns[:3]:  # Show first 3
                print(f"  - {campaign.get('name', 'Unknown')} (ID: {campaign.get('id', 'Unknown')})")
        else:
            print(f"[FAIL] Unexpected response format: {type(campaigns)}")
            return False
    else:
        print(f"[FAIL] Campaigns fetch failed: {response.text}")
        return False
    
    return True

def test_lead_generation_and_download():
    """Test lead generation, preview, and download"""
    print("\n=== Testing Lead Generation & Download ===")
    
    # Start a simple lead generation job
    job_data = {
        'query': 'coffee shops in test city',
        'limit': 5,
        'verify_emails': False,
        'generate_emails': False,
        'export_verified_only': False,
        'advanced_scraping': False,
        'providers': ['google_maps']
    }
    
    print(f"Starting job with query: {job_data['query']}")
    response = requests.post(f"{BASE_URL}/api/generate", json=job_data)
    
    if response.status_code != 200:
        print(f"[FAIL] Failed to start job: {response.text}")
        return False
    
    job_id = response.json().get('job_id')
    print(f"[OK] Job started with ID: {job_id}")
    
    # Poll for job completion
    print("\nPolling for job completion...")
    max_attempts = 30
    for i in range(max_attempts):
        response = requests.get(f"{BASE_URL}/api/status/{job_id}")
        if response.status_code != 200:
            print(f"[FAIL] Failed to get job status: {response.text}")
            return False
        
        data = response.json()
        status = data.get('status')
        progress = data.get('progress', 0)
        
        print(f"  Attempt {i+1}/{max_attempts}: Status={status}, Progress={progress}%")
        
        if status == 'completed':
            print("[OK] Job completed successfully")
            
            # Check lead preview
            leads_preview = data.get('leads_preview', [])
            print(f"\n=== Lead Preview Test ===")
            print(f"Leads in preview: {len(leads_preview)}")
            
            if leads_preview:
                print("[OK] Lead preview contains data")
                print(f"First lead: {json.dumps(leads_preview[0], indent=2)}")
            else:
                print("[FAIL] Lead preview is empty")
            
            # Test download
            print(f"\n=== Download Test ===")
            print(f"Testing download for job: {job_id}")
            
            download_response = requests.get(f"{BASE_URL}/api/download/{job_id}")
            print(f"Download status code: {download_response.status_code}")
            
            if download_response.status_code == 200:
                # Check if we got CSV content
                content_type = download_response.headers.get('Content-Type', '')
                content_length = len(download_response.content)
                
                print(f"Content-Type: {content_type}")
                print(f"Content-Length: {content_length} bytes")
                
                if content_length > 0:
                    # Save to test file
                    test_file = 'test_download.csv'
                    with open(test_file, 'wb') as f:
                        f.write(download_response.content)
                    print(f"[OK] CSV downloaded successfully, saved to {test_file}")
                    
                    # Check CSV content
                    with open(test_file, 'r') as f:
                        lines = f.readlines()
                        print(f"CSV has {len(lines)} lines")
                        if len(lines) > 1:
                            print(f"Headers: {lines[0].strip()}")
                            print("[OK] Download functionality working")
                        else:
                            print("[FAIL] CSV appears to be empty")
                else:
                    print("[FAIL] Downloaded content is empty")
            else:
                print(f"[FAIL] Download failed: {download_response.text}")
                
            return True
            
        elif status == 'error':
            print(f"[FAIL] Job failed with error: {data.get('error')}")
            return False
        
        time.sleep(2)
    
    print("[FAIL] Job timed out")
    return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING R27 INFINITE AI LEADS FIXES")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code != 200:
            print("X Server not responding at", BASE_URL)
            print("Please start the Flask server first: python app.py")
            return
    except requests.exceptions.ConnectionError:
        print("X Cannot connect to server at", BASE_URL)
        print("Please start the Flask server first: python app.py")
        return
    
    print("[OK] Server is running")
    
    # Run tests
    results = []
    
    # Test 1: Instantly API
    instantly_result = test_instantly_api()
    results.append(("Instantly API", instantly_result))
    
    # Test 2: Lead Generation, Preview & Download
    lead_result = test_lead_generation_and_download()
    results.append(("Lead Generation/Download", lead_result))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n[SUCCESS] ALL TESTS PASSED! The fixes are working.")
    else:
        print("\n[WARNING] Some tests failed. Please review the output above.")

if __name__ == "__main__":
    main()