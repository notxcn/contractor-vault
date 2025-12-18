import httpx
import json

API_URL = "http://127.0.0.1:8000/api"

def run_test():
    print("Testing Burn-on-View Tokens...")
    
    # 1. Capture Session
    print("Capturing Session...")
    resp = httpx.post(f"{API_URL}/sessions/", json={
        "name": "Burn Test Session",
        "target_url": "https://example.com",
        "cookies": [{"name": "test", "value": "123", "domain": "example.com", "path": "/"}],
        "created_by": "admin@local.com",
        "is_active": True
    })
    
    if resp.status_code != 201:
        print("Failed to capture:", resp.text)
        return
        
    session_id = resp.json()["id"]
    print(f"Session Captured: {session_id}")
    
    # 2. Generate Burn Token
    print("Generating Burn-on-View Token...")
    token_resp = httpx.post(f"{API_URL}/sessions/generate-token", json={
        "credential_id": session_id,
        "contractor_email": "contractor@burn.test",
        "duration_minutes": 60,
        "admin_email": "admin@local.com",
        "is_one_time": True
    })
    
    if token_resp.status_code != 200:
        print("Failed to generate token:", token_resp.text)
        return
        
    data = token_resp.json()
    claim_token = data['claim_url'].split("/")[-1]
    print(f"Token Generated: {claim_token}")
    
    # 3. First Claim (Should Succeed)
    print("\nAttempting 1st Claim (Should SUCCEED)...")
    claim1 = httpx.post(f"{API_URL}/sessions/claim/{claim_token}")
    
    if claim1.status_code == 200:
        print("✅ 1st Claim Successful!")
    else:
        print(f"❌ 1st Claim Failed: {claim1.status_code} {claim1.text}")
        return

    # 4. Second Claim (Should Fail)
    print("\nAttempting 2nd Claim (Should FAIL 410)...")
    claim2 = httpx.post(f"{API_URL}/sessions/claim/{claim_token}")
    
    if claim2.status_code == 410:
        print("✅ 2nd Claim Failed as expected (410 Gone).")
        print(f"Message: {claim2.json()['detail']}")
    else:
        print(f"❌ 2nd Claim Unexpected Status: {claim2.status_code} {claim2.text}")

if __name__ == "__main__":
    run_test()
