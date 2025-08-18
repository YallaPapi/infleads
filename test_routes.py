import requests
import json

def test_routes():
    """Test various API routes to see which ones work"""
    routes_to_test = [
        ('GET', 'http://localhost:5000/', 'Home page'),
        ('GET', 'http://localhost:5000/api/health', 'Health check'),
        ('POST', 'http://localhost:5000/api/expand-keywords', 'Keyword expansion'),
    ]
    
    for method, url, description in routes_to_test:
        try:
            if method == 'GET':
                response = requests.get(url)
            else:
                test_data = {"keyword": "lawyers", "location": "Las Vegas"}
                response = requests.post(url, json=test_data)
            
            print(f"{description}: {response.status_code}")
            if response.status_code != 200:
                print(f"  Error: {response.text[:100]}...")
        except Exception as e:
            print(f"{description}: ERROR - {e}")
        print()

if __name__ == "__main__":
    test_routes()

