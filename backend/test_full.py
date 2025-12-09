"""Full test: capture session, generate token, claim it."""
import httpx

base = 'http://127.0.0.1:8000'

# Step 1: Get existing sessions
print("Step 1: Getting sessions...")
r = httpx.get(f'{base}/api/sessions/', timeout=10)
sessions = r.json()
if not sessions:
    print("No sessions! Create one first.")
    exit(1)

session = sessions[-1]
print(f"  Using session: {session['name']} ({session['id']})")

# Step 2: Generate token
print("\nStep 2: Generating token...")
r = httpx.post(f'{base}/api/sessions/generate-token', json={
    'credential_id': session['id'],
    'contractor_email': 'test@example.com',
    'duration_minutes': 60,
    'admin_email': 'admin@example.com',
}, timeout=10)

if r.status_code != 200 and r.status_code != 201:
    print(f"  Error: {r.status_code} - {r.text}")
    exit(1)

token_data = r.json()
# Extract token from claim URL
claim_token = token_data['claim_url'].split('/')[-1]
print(f"  Token generated: {claim_token[:20]}...")

# Step 3: Claim token
print("\nStep 3: Claiming token...")
r = httpx.post(f'{base}/api/sessions/claim/{claim_token}', timeout=10)
print(f"  Status: {r.status_code}")
print(f"  Response: {r.text[:300]}...")

if r.status_code == 200:
    print("\n✅ SUCCESS! Full flow works.")
else:
    print("\n❌ FAILED at claim step.")
