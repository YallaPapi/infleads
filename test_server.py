import requests

def test_server():
    """Test if the Flask server is running"""
    try:
        response = requests.get('http://localhost:5000/')
        print(f"Server is running! Status: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("Server is not running or not accessible")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_server()

