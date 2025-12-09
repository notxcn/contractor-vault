"""Store Steam credential and generate token"""
import httpx

BASE_URL = "http://127.0.0.1:8000"

# Store Steam credential
print("Storing Steam credential...")
cred_response = httpx.post(
    f"{BASE_URL}/api/credentials/",
    json={
        "name": "Steam Store",
        "target_url": "https://store.steampowered.com/login",
        "username": "cooperpreston31",
        "password": "!05Qux#%V%836AT6cmA2iBb05e%s4ncFDjvAK",
        "notes": "Steam test account",
        "created_by": "admin@test.com"
    },
    timeout=30
)

print(f"Credential Status: {cred_response.status_code}")
cred = cred_response.json()
print(f"Credential ID: {cred['id']}")

# Generate access token
print("\nGenerating access token...")
token_response = httpx.post(
    f"{BASE_URL}/api/access/generate-access-token",
    json={
        "credential_id": cred["id"],
        "contractor_email": "demo@contractor.com",
        "duration_minutes": 60,
        "admin_email": "admin@test.com",
        "notes": "Live demo test"
    },
    timeout=30
)

print(f"Token Status: {token_response.status_code}")
token = token_response.json()
print(f"\n{'='*60}")
print("ACCESS TOKEN GENERATED!")
print(f"{'='*60}")
print(f"Token ID: {token['token_id']}")
print(f"Claim URL: {token['claim_url']}")
print(f"Claim Token: {token['claim_url'].split('/')[-1]}")
print(f"Expires: {token['expires_at']}")
print(f"{'='*60}")
