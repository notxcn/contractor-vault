"""
Contractor Vault - API Demo Script
Run this to demo the full workflow
"""
import httpx

BASE_URL = "http://127.0.0.1:8000"

def demo():
    print("=" * 60)
    print("CONTRACTOR VAULT - API DEMO")
    print("=" * 60)
    
    # Step 1: Create a credential
    print("\n📦 STEP 1: Creating a credential...")
    credential_data = {
        "name": "AWS Console Demo",
        "target_url": "https://aws.amazon.com/console",
        "username": "demo@company.com",
        "password": "SuperSecret123!",
        "notes": "Demo AWS account for contractors",
        "created_by": "admin@company.com"
    }
    
    response = httpx.post(f"{BASE_URL}/api/credentials/", json=credential_data)
    credential = response.json()
    
    print(f"   ✅ Credential created!")
    print(f"   ID: {credential['id']}")
    print(f"   Name: {credential['name']}")
    print(f"   Target: {credential['target_url']}")
    print(f"   ⚠️ Note: Password is encrypted, never returned in API")
    
    # Step 2: Generate access token
    print("\n🔑 STEP 2: Generating access token for contractor...")
    token_data = {
        "credential_id": credential["id"],
        "contractor_email": "freelancer@example.com",
        "duration_minutes": 60,
        "admin_email": "admin@company.com",
        "notes": "Granting 1-hour access for project work"
    }
    
    response = httpx.post(f"{BASE_URL}/api/access/generate-access-token", json=token_data)
    token = response.json()
    
    print(f"   ✅ Token generated!")
    print(f"   Token ID: {token['token_id']}")
    print(f"   Claim URL: {token['claim_url']}")
    print(f"   Expires: {token['expires_at']}")
    
    # Step 3: Check audit logs
    print("\n📋 STEP 3: Checking audit logs...")
    response = httpx.get(f"{BASE_URL}/api/audit/logs")
    logs = response.json()
    
    print(f"   ✅ Found {logs['total']} audit log entries:")
    for log in logs['logs'][:5]:
        print(f"      - [{log['action']}] {log['actor']} → {log['target_resource'][:40]}...")
    
    # Step 4: Demo kill switch
    print("\n🚨 STEP 4: Testing kill switch...")
    revoke_data = {
        "contractor_email": "freelancer@example.com",
        "admin_email": "admin@company.com",
        "reason": "Demo - Testing kill switch"
    }
    
    response = httpx.post(
        f"{BASE_URL}/api/access/revoke-all/freelancer@example.com", 
        json=revoke_data
    )
    result = response.json()
    
    print(f"   ✅ Kill switch activated!")
    print(f"   Revoked: {result['revoked_count']} tokens")
    print(f"   Message: {result['message']}")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE! All systems working.")
    print("=" * 60)

if __name__ == "__main__":
    demo()
