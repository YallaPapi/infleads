#!/usr/bin/env python3
"""
Test script to verify the query flow fix
Tests that multiple keywords preserve location information
"""

import requests
import json
import time

def test_query_fix():
    """Test that multiple queries preserve location information"""
    
    # Test data - simulating frontend sending multiple keywords with location
    test_data = {
        "query": "restaurants in Austin",  # Original query with location
        "queries": [
            "restaurants in Austin",
            "coffee shops in Austin", 
            "bars in Austin"
        ],  # Multiple queries with preserved location
        "limit": 10,
        "providers": ["openstreetmap"],
        "verify_emails": False,
        "generate_emails": False,
        "export_verified_only": False,
        "advanced_scraping": False,
        "add_to_instantly": False,
        "instantly_campaign": ""
    }
    
    print("=== Testing Query Flow Fix ===")
    print(f"Original query: {test_data['query']}")
    print(f"Multiple queries: {test_data['queries']}")
    print(f"Expected: Each query should contain location 'Austin'")
    print()
    
    try:
        # Send request to Flask API
        response = requests.post(
            "http://localhost:5001/api/generate",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data.get('job_id')
            print(f"SUCCESS: Job created successfully: {job_id}")
            
            # Monitor job progress
            print("Monitoring job progress...")
            for attempt in range(30):  # Wait up to 30 seconds
                status_response = requests.get(f"http://localhost:5001/api/status/{job_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status', 'unknown')
                    leads_count = len(status_data.get('leads', []))
                    
                    print(f"Status: {status}, Leads: {leads_count}")
                    
                    if status == 'completed':
                        if leads_count > 0:
                            print(f"SUCCESS! Found {leads_count} leads")
                            
                            # Show sample lead
                            sample_lead = status_data['leads'][0]
                            print(f"Sample lead: {sample_lead.get('name', 'Unknown')} - {sample_lead.get('address', 'No address')}")
                            return True
                        else:
                            print("FAILED! No leads found - location information may still be lost")
                            return False
                    elif status in ['failed', 'error']:
                        print(f"FAILED! Job failed with status: {status}")
                        return False
                else:
                    print(f"Failed to get job status: {status_response.status_code}")
                    
                time.sleep(1)
            
            print("Timeout waiting for job completion")
            return False
            
        else:
            print(f"FAILED! API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"FAILED! Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_query_fix()
    if success:
        print("\nQUERY FIX TEST PASSED!")
    else:
        print("\nQUERY FIX TEST FAILED!")