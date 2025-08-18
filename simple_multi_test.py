import requests
import json
import time

def simple_multi_test():
    """Simple test with just 2 queries to see debug output"""
    
    print("🔍 SIMPLE MULTI-QUERY TEST")
    print("="*40)
    
    # Use just 2 simple queries
    queries = [
        "personal injury lawyers in Las Vegas",
        "divorce attorneys in Las Vegas"
    ]
    
    lead_gen_data = {
        "query": " | ".join(queries),
        "queries": queries,
        "limit": 10,  # Small limit
        "verify_emails": False,
        "generate_emails": False,
        "export_verified_only": False,
        "advanced_scraping": False
    }
    
    print(f"📋 Testing with {len(queries)} queries, limit {lead_gen_data['limit']} each")
    print(f"    Queries: {queries}")
    
    response = requests.post('http://localhost:5000/api/generate', 
                           json=lead_gen_data,
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code != 200:
        print(f"❌ Request failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    job_id = response.json()['job_id']
    print(f"✅ Job started: {job_id}")
    
    # Monitor briefly
    for i in range(15):  # 30 seconds max
        time.sleep(2)
        status_response = requests.get(f'http://localhost:5000/api/status/{job_id}')
        
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"📊 {status['status']} - {status['progress']}% - {status.get('message', '')}")
            
            if status['status'] in ['completed', 'error']:
                if status['status'] == 'completed':
                    print(f"✅ Final result: {status.get('total_leads', 0)} leads")
                else:
                    print(f"❌ Error: {status.get('error', 'Unknown')}")
                break
        else:
            print(f"❌ Status check failed: {status_response.status_code}")
            break

if __name__ == "__main__":
    time.sleep(3)  # Wait for server
    simple_multi_test()

