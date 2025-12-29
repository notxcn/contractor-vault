import httpx

API = "https://contractor-vault-production.up.railway.app/api"

print("1. Creating session...")
r = httpx.post(f"{API}/sessions/", json={
    "name": "Debug",
    "target_url": "http://x",
    "cookies": [{"name": "a", "value": "b", "domain": "x", "path": "/"}],
    "created_by": "x",
    "is_active": True
}, timeout=30)
print(f"   Status: {r.status_code}")
sid = r.json()["id"]
print(f"   Session ID: {sid}")

print("\n2. Generating token...")
r2 = httpx.post(f"{API}/sessions/generate-token", json={
    "credential_id": sid,
    "contractor_email": "test@x.com",
    "duration_minutes": 60,
    "admin_email": "admin@x.com"
}, timeout=30)
print(f"   Status: {r2.status_code}")
tid = r2.json()["token_id"]
print(f"   Token ID: {tid}")

print("\n3. Revoking token...")
r3 = httpx.post(f"{API}/access/revoke/{tid}", json={
    "token_id": tid,
    "admin_email": "admin@x.com",
    "reason": "test"
}, timeout=30)
print(f"   Status: {r3.status_code}")
print(f"   Response:\n{r3.text}")
