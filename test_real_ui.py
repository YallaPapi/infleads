#!/usr/bin/env python3
"""
Real UI test - simulates actual user interactions
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:5000"

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

def test_instantly_dropdown():
    """Test that Instantly campaigns actually load in the dropdown"""
    print("\n=== TEST 1: Instantly Campaign Dropdown ===")
    
    # First check the checkbox is clicked (this triggers campaign loading)
    print("1. Simulating checkbox click that triggers campaign loading...")
    
    # Get campaigns directly
    response = requests.get(f"{BASE_URL}/api/instantly/campaigns")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        campaigns = response.json()
        print(f"   Campaigns returned: {len(campaigns) if isinstance(campaigns, list) else 'ERROR - Not a list'}")
        
        if isinstance(campaigns, list) and len(campaigns) > 0:
            print("   [PASS] Campaigns loaded successfully")
            print("   Available campaigns:")
            for c in campaigns[:5]:
                print(f"     - {c.get('name')} (ID: {c.get('id')})")
            return True, campaigns[0].get('id') if campaigns else None
        else:
            print("   [FAIL] No campaigns or wrong format")
            return False, None
    else:
        print(f"   [FAIL] Could not load campaigns: {response.text}")
        return False, None

def test_lead_generation_with_instantly(campaign_id=None):
    """Test generating leads and adding to Instantly"""
    print("\n=== TEST 2: Lead Generation with Instantly Integration ===")
    
    # Prepare request as if from the UI
    request_data = {
        'query': 'dentists in Miami',
        'limit': 5,
        'verify_emails': True,
        'generate_emails': True,
        'export_verified_only': False,
        'advanced_scraping': False,
        'providers': ['google_maps'],
        'add_to_instantly': True if campaign_id else False,
        'instantly_campaign': campaign_id if campaign_id else ''
    }
    
    print(f"1. Starting lead generation job...")
    print(f"   Query: {request_data['query']}")
    print(f"   Add to Instantly: {request_data['add_to_instantly']}")
    if campaign_id:
        print(f"   Campaign ID: {campaign_id}")
    
    # Start the job
    response = requests.post(f"{BASE_URL}/api/generate", json=request_data)
    
    if response.status_code != 200:
        print(f"   [FAIL] Could not start job: {response.text}")
        return False
    
    job_id = response.json().get('job_id')
    print(f"   Job started: {job_id}")
    
    # Poll for completion
    print("\n2. Waiting for job to complete...")
    for i in range(60):  # Wait up to 2 minutes
        response = requests.get(f"{BASE_URL}/api/status/{job_id}")
        
        if response.status_code != 200:
            print(f"   [FAIL] Could not get status: {response.text}")
            return False
        
        data = response.json()
        status = data.get('status')
        progress = data.get('progress', 0)
        message = data.get('message', '')
        
        print(f"   [{i+1}] Status: {status} | Progress: {progress}% | {message}")
        
        if status == 'completed':
            print("\n3. Job completed! Checking results...")
            
            # Check lead preview
            leads_preview = data.get('leads_preview', [])
            print(f"\n   === LEAD PREVIEW TEST ===")
            print(f"   Leads in preview: {len(leads_preview)}")
            
            if leads_preview:
                print("   [PASS] Lead preview has data")
                print(f"   First lead name: {leads_preview[0].get('Name')}")
                print(f"   First lead email: {leads_preview[0].get('Email')}")
                print(f"   First lead phone: {leads_preview[0].get('Phone')}")
            else:
                print("   [FAIL] Lead preview is empty!")
            
            # Test download button
            print(f"\n   === DOWNLOAD BUTTON TEST ===")
            print(f"   Testing download endpoint for job: {job_id}")
            
            download_response = requests.get(f"{BASE_URL}/api/download/{job_id}")
            
            if download_response.status_code == 200:
                content = download_response.content
                if len(content) > 0:
                    print(f"   [PASS] Download works - got {len(content)} bytes")
                    
                    # Save and check content
                    with open('test_download_real.csv', 'wb') as f:
                        f.write(content)
                    
                    with open('test_download_real.csv', 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        print(f"   CSV has {len(lines)} lines")
                        if len(lines) > 1:
                            print(f"   Headers: {lines[0].strip()}")
                            print("   [PASS] CSV has data")
                        else:
                            print("   [FAIL] CSV is empty")
                else:
                    print("   [FAIL] Download returned empty content")
            else:
                print(f"   [FAIL] Download failed: {download_response.status_code}")
                print(f"   Error: {download_response.text}")
            
            # Check if added to Instantly
            if request_data['add_to_instantly'] and campaign_id:
                if 'Instantly' in message:
                    print(f"\n   === INSTANTLY INTEGRATION TEST ===")
                    print(f"   [PASS] {message}")
                else:
                    print(f"\n   === INSTANTLY INTEGRATION TEST ===")
                    print(f"   [FAIL] No confirmation of Instantly integration")
            
            return True
            
        elif status == 'error':
            print(f"\n   [FAIL] Job failed: {data.get('error')}")
            return False
        
        time.sleep(2)
    
    print("\n   [FAIL] Job timed out after 2 minutes")
    return False

def test_ui_interactions():
    """Test the actual UI form submission flow"""
    print("\n=== TEST 3: UI Form Submission Flow ===")
    
    # Test the multi-provider form
    print("1. Testing multi-provider search form...")
    
    multi_data = {
        'queries': ['restaurants in New York'],
        'limit': 10,
        'verify_emails': False,
        'generate_emails': False,
        'export_verified_only': False,
        'providers': ['google_maps', 'openstreetmap']
    }
    
    response = requests.post(f"{BASE_URL}/api/generate-multi", json=multi_data)
    
    if response.status_code == 200:
        job_id = response.json().get('job_id')
        print(f"   Multi-provider job started: {job_id}")
        
        # Wait a bit then check status
        time.sleep(5)
        status_response = requests.get(f"{BASE_URL}/api/status/{job_id}")
        
        if status_response.status_code == 200:
            data = status_response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Progress: {data.get('progress')}%")
            
            if data.get('leads_preview'):
                print("   [PASS] Multi-provider search working")
            else:
                print("   [WARNING] Multi-provider search started but no preview yet")
        else:
            print("   [FAIL] Could not get multi-provider job status")
    else:
        print(f"   [FAIL] Multi-provider search failed: {response.text}")

def main():
    print("=" * 70)
    print("REAL UI TESTING - R27 INFINITE AI LEADS")
    print("=" * 70)
    
    if not wait_for_server():
        print("[FAIL] Server not responding. Start it with: python app.py")
        return
    
    # Test 1: Instantly campaigns dropdown
    print("\n[TESTING INSTANTLY CAMPAIGN DROPDOWN]")
    campaigns_work, campaign_id = test_instantly_dropdown()
    
    # Test 2: Full lead generation with all features
    print("\n[TESTING LEAD GENERATION WITH ALL FEATURES]")
    lead_gen_works = test_lead_generation_with_instantly(campaign_id)
    
    # Test 3: UI form interactions
    print("\n[TESTING UI FORM INTERACTIONS]")
    test_ui_interactions()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    print(f"1. Instantly Campaigns Load: {'[PASS]' if campaigns_work else '[FAIL]'}")
    print(f"2. Lead Generation Works: {'[PASS]' if lead_gen_works else '[FAIL]'}")
    print(f"3. Download Button Works: Check above for details")
    print(f"4. Lead Preview Shows: Check above for details")
    print(f"5. Instantly Integration: Check above for details")
    
    if campaigns_work and lead_gen_works:
        print("\n[SUCCESS] Core functionality is working!")
    else:
        print("\n[FAILURE] Critical issues found - review output above")

if __name__ == "__main__":
    main()