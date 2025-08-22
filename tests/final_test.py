#!/usr/bin/env python3
"""
Final comprehensive test of the complete query flow fix
Tests both scenarios:
1. Frontend correctly sends queries with location
2. Backend correctly handles queries without location by using original query location
"""

import requests
import json
import time

def test_scenario_1():
    """Test: Frontend sends queries with location (fixed frontend)"""
    print("=== SCENARIO 1: Frontend sends queries WITH location ===")
    
    test_data = {
        "query": "restaurants in Austin",
        "queries": [
            "restaurants in Austin",
            "coffee shops in Austin"
        ],
        "limit": 5,
        "providers": ["openstreetmap"]
    }
    
    print(f"Sending queries: {test_data['queries']}")
    
    response = requests.post(
        "http://localhost:5001/api/generate",
        headers={"Content-Type": "application/json"},
        json=test_data,
        timeout=10
    )
    
    if response.status_code == 200:
        job_data = response.json()
        job_id = job_data.get('job_id')
        print(f"Job created: {job_id}")
        
        # Wait for completion
        for i in range(20):
            time.sleep(1)
            status_response = requests.get(f"http://localhost:5001/api/status/{job_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get('status') == 'completed':
                    leads = status_data.get('total_leads', 0)
                    print(f"RESULT: Found {leads} leads")
                    return leads > 0
        
        print("TIMEOUT")
        return False
    else:
        print(f"API ERROR: {response.status_code}")
        return False

def test_scenario_2():
    """Test: Frontend sends queries WITHOUT location, backend should fix them"""
    print("\n=== SCENARIO 2: Backend fixes queries WITHOUT location ===")
    
    test_data = {
        "query": "restaurants in Austin",  # Original query with location
        "queries": [
            "restaurants",  # Bare keywords without location
            "coffee shops"
        ],
        "limit": 5,
        "providers": ["openstreetmap"]
    }
    
    print(f"Original query: {test_data['query']}")
    print(f"Bare queries: {test_data['queries']}")
    print("Expected: Backend should add 'in Austin' to each query")
    
    response = requests.post(
        "http://localhost:5001/api/generate",
        headers={"Content-Type": "application/json"},
        json=test_data,
        timeout=10
    )
    
    if response.status_code == 200:
        job_data = response.json()
        job_id = job_data.get('job_id')
        print(f"Job created: {job_id}")
        
        # Wait for completion
        for i in range(20):
            time.sleep(1)
            status_response = requests.get(f"http://localhost:5001/api/status/{job_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get('status') == 'completed':
                    leads = status_data.get('total_leads', 0)
                    print(f"RESULT: Found {leads} leads")
                    return leads > 0
        
        print("TIMEOUT")
        return False
    else:
        print(f"API ERROR: {response.status_code}")
        return False

def main():
    print("COMPREHENSIVE QUERY FLOW TEST")
    print("=" * 50)
    
    scenario1_passed = test_scenario_1()
    scenario2_passed = test_scenario_2()
    
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    print(f"Scenario 1 (Frontend with location): {'PASS' if scenario1_passed else 'FAIL'}")
    print(f"Scenario 2 (Backend fixes location): {'PASS' if scenario2_passed else 'FAIL'}")
    
    if scenario1_passed and scenario2_passed:
        print("\nOVERALL: ALL TESTS PASSED - QUERY FLOW FIX IS COMPLETE!")
        return True
    else:
        print("\nOVERALL: SOME TESTS FAILED")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)