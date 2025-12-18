import httpx
import time

API_URL = "http://127.0.0.1:8000/api"

def run_test():
    print("Testing IP Whitelist on Stored Sessions...")
    
    # 1. Create Stored Session
    print("Creating Stored Session...")
    try:
        session_resp = httpx.post(f"{API_URL}/sessions/", json={
            "name": "Test IP Session",
            "target_url": "https://test.com/dashboard",
            "cookies": [{"name": "Auth", "value": "123", "domain": "test.com", "path": "/"}],
            "created_by": "admin@test.com",
            "is_active": True
        })
        
        if session_resp.status_code != 201:
            print("Failed to create session:", session_resp.status_code, session_resp.text)
            return
        
        session_id = session_resp.json()["id"]
        print(f"Session Created: {session_id}")

        # 2. Test FAIL Case (IP Mismatch)
        print("\n--- Testing IP Mismatch (Should Fail) ---")
        token_resp_fail = httpx.post(f"{API_URL}/sessions/generate-token", json={
            "credential_id": session_id,
            "contractor_email": "bad_ip@test.com",
            "duration_minutes": 10,
            "admin_email": "admin@test.com",
            "allowed_ip": "1.2.3.4" # Arbitrary IP
        })
        
        if token_resp_fail.status_code != 200:
             print("Failed to generate token (fail case):", token_resp_fail.status_code, token_resp_fail.text)
        else:
            token_fail_str = token_resp_fail.json()["access_token"]
            # The token field in DB is what we need to claim. 
            # The response provides 'claim_url'. 
            claim_url = token_resp_fail.json()["claim_url"]
            token_val = claim_url.split("/")[-1]

            # Claim
            claim_resp_fail = httpx.post(f"{API_URL}/sessions/claim/{token_val}")
            print(f"Claim Response Code: {claim_resp_fail.status_code}")
            if claim_resp_fail.status_code == 403:
                 print("✅ Success: Blocked access from mismatched IP.")
            else:
                 print(f"❌ Failed: Expected 403, got {claim_resp_fail.status_code}: {claim_resp_fail.text}")

        # 3. Test SUCCESS Case (IP Match)
        print("\n--- Testing IP Match (Should Succeed) ---")
        token_resp_ok = httpx.post(f"{API_URL}/sessions/generate-token", json={
            "credential_id": session_id,
            "contractor_email": "good_ip@test.com",
            "duration_minutes": 10,
            "admin_email": "admin@test.com",
            "allowed_ip": "127.0.0.1" # Localhost
        })
        
        if token_resp_ok.status_code != 200:
             print("Failed to generate token (success case):", token_resp_ok.status_code, token_resp_ok.text)
        else:
            claim_url = token_resp_ok.json()["claim_url"]
            token_val = claim_url.split("/")[-1]
            
            claim_resp_ok = httpx.post(f"{API_URL}/sessions/claim/{token_val}")
            print(f"Claim Response Code: {claim_resp_ok.status_code}")
            if claim_resp_ok.status_code == 200:
                print("✅ Success: Allowed access from matching IP.")
            else:
                print(f"❌ Failed: Expected 200, got {claim_resp_ok.status_code}: {claim_resp_ok.text}")
                
    except Exception as e:
        print(f"Test Exception: {e}")

if __name__ == "__main__":
    run_test()
