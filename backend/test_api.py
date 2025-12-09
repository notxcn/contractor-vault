"""Test the generate-token endpoint to see actual error."""
import httpx
import json

# Get sessions
sessions_resp = httpx.get('http://127.0.0.1:8000/api/sessions/', timeout=10)
sessions = sessions_resp.json()

if not sessions:
    print("No sessions found!")
    exit(1)

session_id = sessions[-1]['id']
print(f"Testing with session ID: {session_id}")

# Try to generate token
try:
    resp = httpx.post(
        'http://127.0.0.1:8000/api/sessions/generate-token',
        json={
            'credential_id': session_id,
            'contractor_email': 'test@gmail.com',
            'duration_minutes': 60,
            'admin_email': 'admin@gmail.com',
        },
        timeout=30
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
