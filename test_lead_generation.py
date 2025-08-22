#!/usr/bin/env python3
"""
Comprehensive test suite for InfLeads lead generation functionality
Tests all critical paths and providers
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:5001"

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_api_health():
    """Test if API is responsive"""
    print_section("Testing API Health")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def test_simple_lead_generation():
    """Test basic lead generation with a simple query"""
    print_section("Testing Simple Lead Generation")
    
    # Simple test query for restaurants in New York
    payload = {
        "query": "restaurants",
        "location": "New York, NY",
        "limit": 5,
        "provider": "auto"  # Uses free providers
    }
    
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Submit job
        response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Failed to submit job: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
        job_data = response.json()
        job_id = job_data.get('job_id')
        print(f"✅ Job submitted successfully. Job ID: {job_id}")
        
        # Poll for results
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/status/{job_id}")
            
            if status_response.status_code != 200:
                print(f"❌ Failed to get status: {status_response.status_code}")
                return None
                
            status_data = status_response.json()
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            
            print(f"  Attempt {attempt + 1}/{max_attempts}: Status={status}, Progress={progress}%")
            
            if status == 'completed':
                leads = status_data.get('results', [])
                print(f"\n✅ Job completed! Found {len(leads)} leads")
                
                # Display first few leads
                for i, lead in enumerate(leads[:3], 1):
                    print(f"\n  Lead {i}:")
                    print(f"    Name: {lead.get('name', 'N/A')}")
                    print(f"    Address: {lead.get('address', 'N/A')}")
                    print(f"    Phone: {lead.get('phone', 'N/A')}")
                    print(f"    Website: {lead.get('website', 'N/A')}")
                    print(f"    Rating: {lead.get('rating', 'N/A')}")
                
                return leads
                
            elif status == 'failed':
                error = status_data.get('error', 'Unknown error')
                print(f"❌ Job failed: {error}")
                return None
        
        print("❌ Job timed out after 60 seconds")
        return None
        
    except Exception as e:
        print(f"❌ Error during lead generation: {e}")
        return None

def test_multiple_locations():
    """Test lead generation with multiple locations"""
    print_section("Testing Multiple Location Queries")
    
    test_queries = [
        {"query": "coffee shops", "location": "San Francisco, CA", "limit": 3},
        {"query": "dentists", "location": "Chicago, IL", "limit": 3},
        {"query": "plumbers", "location": "Austin, TX", "limit": 3}
    ]
    
    results = {}
    for test in test_queries:
        print(f"\nTesting: {test['query']} in {test['location']}")
        
        payload = {**test, "provider": "auto"}
        
        try:
            response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=10)
            
            if response.status_code == 200:
                job_id = response.json().get('job_id')
                print(f"  Job ID: {job_id}")
                
                # Wait briefly then check status
                time.sleep(5)
                status_response = requests.get(f"{BASE_URL}/api/status/{job_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    
                    if status == 'completed':
                        leads = status_data.get('results', [])
                        results[test['location']] = len(leads)
                        print(f"  ✅ Found {len(leads)} leads")
                    else:
                        print(f"  ⏳ Status: {status}")
                        results[test['location']] = 'pending'
            else:
                print(f"  ❌ Failed: {response.status_code}")
                results[test['location']] = 'failed'
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[test['location']] = 'error'
    
    return results

def test_csv_export():
    """Test CSV export functionality"""
    print_section("Testing CSV Export")
    
    # First generate some leads
    payload = {
        "query": "hotels",
        "location": "Miami, FL",
        "limit": 5,
        "provider": "auto"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=10)
        
        if response.status_code == 200:
            job_id = response.json().get('job_id')
            print(f"Job submitted: {job_id}")
            
            # Wait for completion
            time.sleep(10)
            
            # Try to export as CSV
            export_response = requests.get(f"{BASE_URL}/api/export/{job_id}")
            
            if export_response.status_code == 200:
                # Check if response is CSV
                content_type = export_response.headers.get('content-type', '')
                if 'csv' in content_type.lower():
                    print("✅ CSV export successful")
                    print(f"  CSV size: {len(export_response.content)} bytes")
                    # Show first few lines
                    lines = export_response.text.split('\n')[:3]
                    for line in lines:
                        print(f"  {line[:100]}...")
                    return True
                else:
                    print(f"❌ Unexpected content type: {content_type}")
                    return False
            else:
                print(f"❌ Export failed: {export_response.status_code}")
                return False
        else:
            print(f"❌ Job submission failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_provider_availability():
    """Check which providers are available and working"""
    print_section("Testing Provider Availability")
    
    providers_to_test = ["auto", "pure", "hybrid", "free", "yellowpages", "openstreetmap"]
    working_providers = []
    
    for provider in providers_to_test:
        print(f"\nTesting provider: {provider}")
        
        payload = {
            "query": "restaurants",
            "location": "Boston, MA",
            "limit": 2,
            "provider": provider
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=10)
            
            if response.status_code == 200:
                job_id = response.json().get('job_id')
                time.sleep(3)
                
                status_response = requests.get(f"{BASE_URL}/api/status/{job_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get('status') != 'failed':
                        print(f"  ✅ Provider '{provider}' is working")
                        working_providers.append(provider)
                    else:
                        error = status_data.get('error', 'Unknown error')
                        print(f"  ❌ Provider '{provider}' failed: {error}")
            else:
                print(f"  ❌ Provider '{provider}' request failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Provider '{provider}' error: {e}")
    
    return working_providers

def run_all_tests():
    """Run comprehensive test suite"""
    print("\n" + "="*60)
    print("  INFLEADS COMPREHENSIVE LEAD GENERATION TEST SUITE")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    results = {
        'api_health': False,
        'simple_generation': False,
        'multiple_locations': False,
        'csv_export': False,
        'working_providers': []
    }
    
    # Run tests
    results['api_health'] = test_api_health()
    
    if results['api_health']:
        leads = test_simple_lead_generation()
        results['simple_generation'] = leads is not None and len(leads) > 0
        
        location_results = test_multiple_locations()
        results['multiple_locations'] = location_results
        
        results['csv_export'] = test_csv_export()
        
        results['working_providers'] = test_provider_availability()
    
    # Print summary
    print_section("TEST SUMMARY")
    
    print("\n📊 Results:")
    print(f"  API Health:          {'✅ PASS' if results['api_health'] else '❌ FAIL'}")
    print(f"  Lead Generation:     {'✅ PASS' if results['simple_generation'] else '❌ FAIL'}")
    print(f"  CSV Export:          {'✅ PASS' if results['csv_export'] else '❌ FAIL'}")
    print(f"  Working Providers:   {len(results['working_providers'])}")
    
    if results['working_providers']:
        print(f"    Available: {', '.join(results['working_providers'])}")
    
    if results['multiple_locations']:
        print("\n  Location Tests:")
        for location, count in results['multiple_locations'].items():
            status = '✅' if isinstance(count, int) and count > 0 else '❌'
            print(f"    {status} {location}: {count}")
    
    # Overall status
    print("\n" + "="*60)
    if results['api_health'] and results['simple_generation']:
        print("  ✅ SYSTEM IS OPERATIONAL - Lead generation is working!")
    else:
        print("  ❌ SYSTEM HAS ISSUES - Lead generation needs attention")
    print("="*60)
    
    return results

if __name__ == "__main__":
    results = run_all_tests()
    sys.exit(0 if results['simple_generation'] else 1)