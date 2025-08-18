import requests
import time

# Quick test to trigger debug logs
payload = {
    "query": "lawyers in Las Vegas | attorneys in Las Vegas",
    "queries": ["lawyers in Las Vegas", "attorneys in Las Vegas"],
    "limit": 5,
    "verify_emails": False,
    "generate_emails": False,
    "export_verified_only": False,
    "advanced_scraping": False
}

print("🚀 Starting quick test...")
response = requests.post('http://localhost:5000/api/generate', json=payload)
if response.status_code == 200:
    job_id = response.json()['job_id']
    print(f"✅ Job started: {job_id}")
    
    # Wait a bit for processing
    time.sleep(10)
    
    # Check final status
    status_response = requests.get(f'http://localhost:5000/api/status/{job_id}')
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"📊 Final status: {status['status']} - {status.get('total_leads', 0)} leads")
    else:
        print("❌ Status check failed")
else:
    print(f"❌ Request failed: {response.status_code}")
    print(response.text)

