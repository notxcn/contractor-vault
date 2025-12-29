import requests
import json
import sys
import uuid

BASE_URL = "http://localhost:8001"
ADMIN_EMAIL = "admin@company.com"

def print_result(name, success, payload=None):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {name}")
    if not success and payload:
        print(f"   Error: {payload}")

def test_secrets_flow():
    print("\n--- Testing Secrets Management Flow ---")
    
    # 1. Create Secret
    secret_payload = {
        "name": f"E2E Test Secret {uuid.uuid4().hex[:6]}",
        "value": "sk_test_123456789",
        "secret_type": "api_key",
        "description": "Integration test secret",
        "metadata": {"provider": "stripe"}
    }
    
    res = requests.post(f"{BASE_URL}/api/secrets", json=secret_payload, headers={"X-Admin-Email": ADMIN_EMAIL})
    if res.status_code != 200:
        print_result("Create Secret", False, res.text)
        return
    
    secret_id = res.json()["id"]
    print_result("Create Secret", True)
    
    # 2. Share Secret
    share_payload = {
        "secret_id": secret_id,
        "contractor_email": "contractor@test.com",
        "duration_minutes": 15,
        "max_uses": 1
    }
    
    res = requests.post(f"{BASE_URL}/api/secrets/share", json=share_payload, headers={"X-Admin-Email": ADMIN_EMAIL})
    if res.status_code != 200:
        print_result("Share Secret", False, res.text)
        return
        
    token = res.json()["token"]
    print_result("Share Secret", True)
    
    # 3. Claim Secret (Simulating Extension with Device Context)
    device_context = {
        "os": "mac",
        "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "screen": {"width": 1920, "height": 1080}
    }
    
    res = requests.post(
        f"{BASE_URL}/api/secrets/claim/{token}", 
        headers={"X-Device-Context": json.dumps(device_context)}
    )
    
    if res.status_code != 200:
        print_result("Claim Secret", False, res.text)
        return
        
    claimed_value = res.json()["value"]
    if claimed_value == "sk_test_123456789":
        print_result("Verify Secret Value", True)
    else:
        print_result("Verify Secret Value", False, f"Expected sk_test_123456789, got {claimed_value}")

def test_device_trust():
    print("\n--- Testing Device Trust ---")
    
    # List devices (should have been created by the claim above)
    res = requests.get(f"{BASE_URL}/api/devices", headers={"X-Admin-Email": ADMIN_EMAIL})
    if res.status_code == 200:
        devices = res.json()["devices"]
        if len(devices) > 0:
            print_result("Device Registration", True)
            print(f"   Found {len(devices)} devices. Latest: {devices[0]['os']} {devices[0]['browser']}")
            
            # Test Blocking
            device_id = devices[0]["id"]
            res = requests.post(f"{BASE_URL}/api/devices/{device_id}/block", headers={"X-Admin-Email": ADMIN_EMAIL})
            if res.status_code == 200:
                print_result("Block Device", True)
            else:
                print_result("Block Device", False, res.text)
        else:
            print_result("Device Registration", False, "No devices found (Claim step might have failed to register)")
    else:
        print_result("List Devices", False, res.text)

def test_saas_discovery():
    print("\n--- Testing SaaS Discovery ---")
    
    # 1. Seed Apps (if not already)
    requests.post(f"{BASE_URL}/api/discovery/seed")
    
    # 2. Manual Detection
    payload = {
        "contractor_email": "shadow@test.com",
        "service_name": "UnknownApp " + uuid.uuid4().hex[:4]
    }
    
    res = requests.post(f"{BASE_URL}/api/discovery/detections/manual", json=payload)
    if res.status_code == 200:
        print_result("Report Shadow IT", True)
    else:
        print_result("Report Shadow IT", False, res.text)
        
    # 3. Get Dashboard Summary
    res = requests.get(f"{BASE_URL}/api/discovery/report")
    if res.status_code == 200:
        print_result("Get Discovery Report", True)
    else:
        print_result("Get Discovery Report", False, res.text)

if __name__ == "__main__":
    try:
        # Wait for server to start (up to 10s)
        import time
        max_retries = 10
        print("Waiting for server to start...")
        for i in range(max_retries):
            try:
                requests.get(f"{BASE_URL}/health", timeout=1)
                break
            except requests.exceptions.ConnectionError:
                if i == max_retries - 1:
                    raise
                time.sleep(1)
        
        test_secrets_flow()
        test_device_trust()
        test_saas_discovery()
        print("\n✅ E2E Tests Completed")
    except requests.exceptions.ConnectionError:
        print("❌ Error: Backend server is not running at http://localhost:8000")
        print("   Please run: cd backend && python -m uvicorn app.main:app --reload")
        sys.exit(1)
