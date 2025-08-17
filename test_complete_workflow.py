#!/usr/bin/env python3
"""
Complete workflow test - simulates frontend exactly
"""

import requests
import json
import time

def test_complete_workflow():
    base_url = "http://localhost:5000"
    
    print("="*60)
    print("COMPLETE FRONTEND WORKFLOW TEST")
    print("="*60)
    
    # Test 1: Frontend loads
    print("\n1. Testing frontend load...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200 and "R27 Infinite AI Leads Agent" in response.text:
            print("✅ Frontend loads successfully")
        else:
            print(f"❌ Frontend failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend load error: {e}")
        return False
    
    # Test 2: API generate endpoint
    print("\n2. Testing API generate endpoint...")
    try:
        payload = {
            "query": "test coffee shop miami",
            "limit": 2,
            "verify_emails": False
        }
        
        response = requests.post(
            f"{base_url}/api/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            job_id = data.get("job_id")
            print(f"✅ Job started successfully: {job_id}")
        else:
            print(f"❌ API generate failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API generate error: {e}")
        return False
    
    # Test 3: Status polling
    print("\n3. Testing status polling...")
    try:
        for i in range(30):  # Poll for 30 seconds max
            response = requests.get(f"{base_url}/api/status/{job_id}")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                progress = data.get("progress", 0)
                message = data.get("message", "")
                
                print(f"   Status: {status} ({progress}%) - {message}")
                
                if status == "completed":
                    print("✅ Job completed successfully")
                    
                    # Check results
                    leads = data.get("leads_preview", [])
                    if leads:
                        print(f"✅ Found {len(leads)} leads")
                        lead = leads[0]
                        print(f"   Sample lead: {lead.get('Name')} - {lead.get('Phone')}")
                        
                        if lead.get('Name') != 'NA':
                            print("✅ Lead data properly populated")
                        else:
                            print("❌ Lead data still showing NA")
                            return False
                    else:
                        print("❌ No leads in preview")
                        return False
                    
                    break
                elif status == "error":
                    error = data.get("error", "Unknown error")
                    print(f"❌ Job failed: {error}")
                    return False
                    
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return False
                
            time.sleep(1)
        else:
            print("❌ Job timed out")
            return False
            
    except Exception as e:
        print(f"❌ Status polling error: {e}")
        return False
    
    # Test 4: Download CSV
    print("\n4. Testing CSV download...")
    try:
        csv_file = data.get("result_file")
        if csv_file:
            print(f"✅ CSV file created: {csv_file}")
            
            response = requests.get(f"{base_url}/api/download/{job_id}")
            if response.status_code == 200:
                print("✅ CSV download works")
                
                # Check CSV content
                csv_content = response.text
                if "Name,Address,Phone" in csv_content:
                    print("✅ CSV has proper headers")
                    
                    lines = csv_content.strip().split('\n')
                    if len(lines) > 1:  # Header + at least one data row
                        print(f"✅ CSV has {len(lines)-1} data rows")
                        return True
                    else:
                        print("❌ CSV has no data rows")
                        return False
                else:
                    print("❌ CSV missing proper headers")
                    return False
            else:
                print(f"❌ CSV download failed: {response.status_code}")
                return False
        else:
            print("❌ No CSV file in response")
            return False
            
    except Exception as e:
        print(f"❌ CSV download error: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    
    print("\n" + "="*60)
    if success:
        print("🎉 ALL TESTS PASSED - FRONTEND IS WORKING!")
    else:
        print("❌ TESTS FAILED - FRONTEND HAS ISSUES")
    print("="*60)