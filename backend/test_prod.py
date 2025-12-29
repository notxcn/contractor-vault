import httpx
import sys

API_URL = "https://contractor-vault-production.up.railway.app/api"

def test_prod():
    print(f"Testing Production API: {API_URL}")
    
    # 1. Create Dummy Session
    print("Creating Session...")
    try:
        resp = httpx.post(f"{API_URL}/sessions/", json={
            "name": "Prod Test Session",
            "target_url": "https://example.com",
            "cookies": [{"name": "test", "value": "123", "domain": "example.com", "path": "/"}],
            "created_by": "tester@test.com",
            "is_active": True
        }, timeout=10.0)
    except Exception as e:
        print(f"Connection Failed: {e}")
        return False

    if resp.status_code != 201:
        print(f"❌ Create Session Failed: {resp.status_code} {resp.text}")
        return False

    session_id = resp.json()["id"]
    print(f"✅ Session Created: {session_id}")

    # 2. Generate Burn Token
    print("Generating Token with is_one_time=True...")
    token_resp = httpx.post(f"{API_URL}/sessions/generate-token", json={
        "credential_id": session_id,
        "contractor_email": "tester@test.com",
        "duration_minutes": 10,
        "admin_email": "tester@test.com",
        "is_one_time": True
    }, timeout=10.0)

    if token_resp.status_code == 200:
        print("✅ Token Generated Successfully!")
        data = token_resp.json()
        print(f"Token URL: {data.get('claim_url')}")
        # Verify if API returned 200 that it ACCEPTED 'is_one_time' 
        # (If Pydantic ignored it, it would still return 200 but functionality missing).
        # We can't verify 'is_one_time' persistence without claiming or checking list.
        # But 200 means at least no Schema Validation Error.
        return True
    elif token_resp.status_code == 422:
        print("❌ 422 Unprocessable Entity - Likely Schema Mismatch (is_one_time unknown)")
        print(token_resp.text)
        return False
    else:
        print(f"❌ Generate Failed: {token_resp.status_code} {token_resp.text}")
        return False

if __name__ == "__main__":
    if test_prod():
        sys.exit(0)
    else:
        sys.exit(1)
