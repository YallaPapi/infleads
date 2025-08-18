import requests
import json
import time

def test_full_workflow():
    """Test the complete workflow: keyword expansion + lead generation"""
    
    print("🚀 TESTING COMPLETE WORKFLOW")
    print("="*50)
    
    # Step 1: Expand keywords
    print("\n1. Testing Keyword Expansion...")
    expansion_data = {
        "keyword": "lawyers", 
        "location": "Las Vegas"
    }
    
    response = requests.post('http://localhost:5000/api/expand-keywords', 
                           json=expansion_data,
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code != 200:
        print(f"❌ Keyword expansion failed: {response.status_code}")
        return False
    
    expansion_result = response.json()
    print(f"✅ Generated {expansion_result['count']} keyword variants")
    
    # Select first 3 keywords for testing
    selected_keywords = [v['keyword'] for v in expansion_result['variants'][:3]]
    print(f"📋 Selected keywords: {selected_keywords}")
    
    # Step 2: Test lead generation with multiple keywords
    print("\n2. Testing Lead Generation with Multiple Keywords...")
    
    # Simulate frontend sending multiple queries
    lead_gen_data = {
        "query": " | ".join(selected_keywords),  # Combined query
        "queries": selected_keywords,  # Individual queries
        "limit": 10,  # Small limit for testing
        "verify_emails": False,  # Skip email verification for speed
        "generate_emails": False,  # Skip email generation for speed
        "export_verified_only": False,
        "advanced_scraping": False
    }
    
    response = requests.post('http://localhost:5000/api/generate', 
                           json=lead_gen_data,
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code != 200:
        print(f"❌ Lead generation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    job_data = response.json()
    job_id = job_data['job_id']
    print(f"✅ Lead generation job started: {job_id}")
    
    # Step 3: Monitor job progress
    print("\n3. Monitoring Job Progress...")
    max_attempts = 60  # 60 seconds timeout
    attempt = 0
    
    while attempt < max_attempts:
        response = requests.get(f'http://localhost:5000/api/status/{job_id}')
        if response.status_code != 200:
            print(f"❌ Status check failed: {response.status_code}")
            return False
        
        status = response.json()
        print(f"📊 Status: {status['status']} - Progress: {status['progress']}% - {status.get('message', '')}")
        
        if status['status'] == 'completed':
            print(f"✅ Job completed! Found {status.get('total_leads', 0)} total leads")
            
            # Show preview of results
            if status.get('leads_preview'):
                print(f"📋 Preview of first few leads:")
                for i, lead in enumerate(status['leads_preview'][:3], 1):
                    print(f"  {i}. {lead.get('Name', 'N/A')} - {lead.get('Phone', 'N/A')} - {lead.get('Email', 'N/A')}")
            
            return True
            
        elif status['status'] == 'error':
            print(f"❌ Job failed: {status.get('error', 'Unknown error')}")
            return False
        
        time.sleep(2)
        attempt += 1
    
    print("❌ Job timed out")
    return False

if __name__ == "__main__":
    success = test_full_workflow()
    print(f"\n{'='*50}")
    print(f"🎯 WORKFLOW TEST: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"{'='*50}")

