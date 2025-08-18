import requests
import json

def debug_request():
    """Debug what exactly we're sending to the server"""
    
    print("🔍 DEBUGGING REQUEST PAYLOAD")
    print("="*40)
    
    # Simulate exactly what the frontend should send
    queries = [
        "personal injury lawyers in Las Vegas",
        "divorce attorneys in Las Vegas"
    ]
    
    payload = {
        "query": " | ".join(queries),  # Combined query string
        "queries": queries,            # Array of individual queries
        "limit": 10,
        "verify_emails": False,
        "generate_emails": False,
        "export_verified_only": False,
        "advanced_scraping": False
    }
    
    print("📤 Sending payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post('http://localhost:5000/api/generate', 
                           json=payload,
                           headers={'Content-Type': 'application/json'})
    
    print(f"\n📥 Response status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Response:", json.dumps(result, indent=2))
    else:
        print("Response text:", response.text)

if __name__ == "__main__":
    debug_request()

