
import requests
import time

API_URL = "http://localhost:8000/api/auth/password-login"

def test_rate_limit():
    print(f"Testing rate limit on {API_URL}")
    print("Limit is 5 requests per minute.")
    
    # Payload (wrong password is fine, we just want to trigger the endpoint)
    payload = {
        "email": "admin@contractorvault.com",
        "password": "wrongpassword"
    }
    
    for i in range(1, 10):
        try:
            response = requests.post(API_URL, json=payload)
            print(f"Request {i}: Status Code {response.status_code}")
            
            if response.status_code == 429:
                print("✅ Rate limit triggered successfully (429 Too Many Requests)")
                return
            
        except Exception as e:
            print(f"Request {i} failed: {e}")
            
        # time.sleep(0.1) 
    
    print("❌ Rate limit NOT triggered after 10 requests")

if __name__ == "__main__":
    test_rate_limit()
