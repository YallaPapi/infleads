#!/usr/bin/env python3
"""
Final test of email generation toggle - no hanging commands
"""

import requests
import json
import time
import subprocess
import signal
import os

def start_flask():
    """Start Flask server"""
    return subprocess.Popen(['python', 'app.py'], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)

def test_toggle():
    """Test the toggle functionality"""
    base_url = "http://localhost:5000"
    
    # Test with emails DISABLED
    print("Testing email generation DISABLED...")
    payload = {
        "query": "dentist colorado springs", 
        "limit": 1,
        "verify_emails": False,
        "generate_emails": False
    }
    
    response = requests.post(f"{base_url}/api/generate", json=payload)
    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        return False
    
    job_id = response.json()['job_id']
    print(f"Job started: {job_id}")
    
    # Poll for completion
    for _ in range(30):
        response = requests.get(f"{base_url}/api/status/{job_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'completed':
                leads = data.get('leads_preview', [])
                if leads:
                    email_content = leads[0].get('DraftEmail', '')
                    if email_content == 'Email generation disabled':
                        print("✅ SUCCESS: Email generation properly disabled!")
                        return True
                    else:
                        print(f"❌ FAIL: Got email content when disabled: {email_content[:50]}...")
                        return False
                break
            elif data.get('status') == 'error':
                print(f"❌ Job failed: {data.get('error')}")
                return False
        time.sleep(2)
    
    print("❌ Timeout")
    return False

if __name__ == "__main__":
    # Start Flask
    flask_proc = start_flask()
    time.sleep(3)  # Wait for startup
    
    try:
        success = test_toggle()
        if success:
            print("\n🎉 EMAIL GENERATION TOGGLE WORKING!")
        else:
            print("\n❌ Toggle not working properly")
    finally:
        # Clean shutdown
        flask_proc.terminate()
        flask_proc.wait(timeout=5)
