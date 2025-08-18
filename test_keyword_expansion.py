import requests
import json

def test_keyword_expansion():
    """Test the keyword expansion API endpoint"""
    try:
        # Test data
        test_data = {
            "keyword": "lawyers",
            "location": "Las Vegas"
        }
        
        print("Testing keyword expansion...")
        print(f"Input: {test_data}")
        
        response = requests.post('http://localhost:5000/api/expand-keywords', 
                               json=test_data,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nSuccess! Generated {result['count']} keyword variants:")
            for i, variant in enumerate(result['variants'][:10], 1):  # Show first 10
                print(f"{i}. {variant['keyword']} - {variant['description']}")
            
            if result['count'] > 10:
                print(f"... and {result['count'] - 10} more variants")
                
            return True
        else:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the Flask server. Is it running?")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_keyword_expansion()

