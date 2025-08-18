#!/usr/bin/env python3

import requests
import json
import time
import subprocess
import signal
import os
from threading import Thread

def run_server():
    """Run the Flask server"""
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output
    subprocess.run(['python', 'app.py'], env=env)

def test_multi_query():
    """Test multi-query functionality"""
    
    print("🚀 FINAL DEBUG TEST")
    print("="*50)
    
    # Start server in background
    print("📡 Starting Flask server...")
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(6)  # Wait for server to fully start
    
    # Test payload
    payload = {
        "query": "lawyers in Las Vegas | attorneys in Las Vegas",
        "queries": ["lawyers in Las Vegas", "attorneys in Las Vegas"],
        "limit": 3,  # Small limit to make it obvious
        "verify_emails": False,
        "generate_emails": False,
        "export_verified_only": False,
        "advanced_scraping": False
    }
    
    print(f"📤 Sending request with {len(payload['queries'])} queries, limit {payload['limit']} each")
    print(f"    Expected result: Up to {len(payload['queries']) * payload['limit']} total leads")
    
    try:
        response = requests.post('http://localhost:5000/api/generate', json=payload)
        
        if response.status_code == 200:
            job_id = response.json()['job_id']
            print(f"✅ Job started: {job_id}")
            
            # Monitor job
            for i in range(20):  # 40 seconds max
                time.sleep(2)
                status_response = requests.get(f'http://localhost:5000/api/status/{job_id}')
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"📊 {status['status']} - {status['progress']}% - {status.get('message', '')}")
                    
                    if status['status'] in ['completed', 'error']:
                        if status['status'] == 'completed':
                            total = status.get('total_leads', 0)
                            print(f"\n🎯 FINAL RESULT:")
                            print(f"   Total leads: {total}")
                            print(f"   Expected: {len(payload['queries']) * payload['limit']} (if working correctly)")
                            
                            if total > payload['limit']:
                                print(f"✅ SUCCESS: Multi-query is working! Got more than single query limit.")
                            else:
                                print(f"❌ ISSUE: Only got {total} leads, same as single query limit.")
                                
                        else:
                            print(f"❌ Job failed: {status.get('error', 'Unknown error')}")
                        break
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    break
            else:
                print("⏰ Job monitoring timed out")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n{'='*50}")
    print("🏁 FINAL DEBUG TEST COMPLETE")

if __name__ == "__main__":
    test_multi_query()

