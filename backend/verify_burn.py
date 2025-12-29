import httpx
import sys
import time

API_URL = "https://contractor-vault-production.up.railway.app/api"

def verify_burn_flow():
    print(f"🔥 Testing Burn-on-View Flow on: {API_URL}")
    
    # 1. Create Session
    print("\n1. Creating Session...")
    try:
        session_resp = httpx.post(f"{API_URL}/sessions/", json={
            "name": "Burn Test Session",
            "target_url": "https://example.com/login",
            "cookies": [{"name": "auth", "value": "secret123", "domain": "example.com", "path": "/"}],
            "created_by": "qa@example.com",
            "is_active": True
        })
        session_resp.raise_for_status()
        session_id = session_resp.json()["id"]
        print(f"✅ Session Created: {session_id}")
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        return False

    # 2. Generate Burn Token
    print("\n2. Generating Burn Token (is_one_time=True)...")
    try:
        token_resp = httpx.post(f"{API_URL}/sessions/generate-token", json={
            "credential_id": session_id,
            "contractor_email": "qa@example.com",
            "duration_minutes": 5,
            "admin_email": "admin@example.com",
            "is_one_time": True
        })
        token_resp.raise_for_status()
        token_data = token_resp.json()
        claim_url = token_data["claim_url"]
        # Extract token string usually at end of URL
        # URL format: .../claim/{token}
        token_str = claim_url.split("/")[-1]
        print(f"✅ Token Generated: {token_str}")
        print(f"   URL: {claim_url}")
    except Exception as e:
        print(f"❌ Failed to generate token: {e}")
        return False

    # 3. First Claim (Should Succeed)
    print("\n3. Claiming Token (1st time)...")
    try:
        # We hit the API endpoint that the Frontend would hit?
        # The 'claim_url' points to Frontend .../claim/{token}
        # The Frontend calls GET /api/sessions/claim/{token}
        # We simulate the API call directly.
        
        api_claim_url = f"{API_URL}/sessions/claim/{token_str}"
        claim_resp = httpx.post(api_claim_url)
        
        if claim_resp.status_code == 200:
            print("✅ 1st Claim Successful (200 OK)")
            print(f"   Response: {claim_resp.json()}")
        else:
            print(f"❌ 1st Claim Failed: {claim_resp.status_code}")
            print(claim_resp.text)
            return False
    except Exception as e:
        print(f"❌ Error during 1st claim: {e}")
        return False

    # 4. Second Claim (Should Fail)
    print("\n4. Claiming Token (2nd time)...")
    try:
        claim_resp_2 = httpx.post(api_claim_url)
        
        if claim_resp_2.status_code == 410:
            print("✅ 2nd Claim correctly blocked (410 Gone)")
        else:
            print(f"❌ 2nd Claim NOT blocked! Status: {claim_resp_2.status_code}")
            print(claim_resp_2.text)
            return False
    except Exception as e:
        print(f"❌ Error during 2nd claim: {e}")
        return False

    print("\n✨ BURN-ON-VIEW VERIFICATION PASSED! ✨")
    return True

if __name__ == "__main__":
    if verify_burn_flow():
        sys.exit(0)
    else:
        sys.exit(1)
