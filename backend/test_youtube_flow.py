import httpx
import json

API_URL = "http://127.0.0.1:8000/api"

cookies = [
    {
      "name": "__Secure-3PAPISID",
      "value": "YOjS3ulGsM1BFX4T/AdYLIGdJ3a9QuGxlN",
      "domain": ".youtube.com",
      "path": "/"
    },
    {
      "name": "PREF",
      "value": "tz=America.New_York",
      "domain": ".youtube.com",
      "path": "/"
    }
]

def run_test():
    print("Capturing YouTube Session...")
    try:
        resp = httpx.post(f"{API_URL}/sessions/", json={
            "name": "YouTube Session (Simulated)",
            "target_url": "https://www.youtube.com",
            "cookies": cookies,
            "created_by": "admin@local.com",
            "is_active": True
        })
        
        if resp.status_code != 201:
            print("Failed to capture:", resp.text)
            return
            
        session_id = resp.json()["id"]
        print(f"Session Captured: {session_id}")
        
        print("Generating Token...")
        token_resp = httpx.post(f"{API_URL}/sessions/generate-token", json={
            "credential_id": session_id,
            "contractor_email": "contractor@youtube.test",
            "duration_minutes": 60,
            "admin_email": "admin@local.com",
            "allowed_ip": "127.0.0.1"
        })
        
        if token_resp.status_code != 200:
            print("Failed to generate token:", token_resp.text)
            return
            
        data = token_resp.json()
        print("✅ Token Generated Successfully!")
        print(f"Claim URL: {data['claim_url']}")
        print(f"Access Token: {data['access_token']}")
        
        print("\nVerifying Claim...")
        claim_token = data['claim_url'].split("/")[-1]
        claim_resp = httpx.post(f"{API_URL}/sessions/claim/{claim_token}")
        
        if claim_resp.status_code == 200:
            print("✅ Claim Successful! Cookies retrieved.")
            c_data = claim_resp.json()
            print(f"Cookies Count: {len(c_data['cookies'])}")
            print(f"Session Name: {c_data['session_name']}")
        else:
            print("❌ Claim Failed:", claim_resp.text)

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    run_test()
