"""
Contractor Vault - Comprehensive Production Test
Tests all core features against the live Railway API.
"""
import httpx
import sys

API_URL = "https://contractor-vault-production.up.railway.app/api"

def test_all():
    print("=" * 60)
    print("🔒 CONTRACTOR VAULT - COMPREHENSIVE PRODUCTION TEST")
    print(f"   Target: {API_URL}")
    print("=" * 60)
    
    results = []
    
    # ==================== TEST 1: Session Creation ====================
    print("\n[1/6] Testing Session Creation...")
    try:
        resp = httpx.post(f"{API_URL}/sessions/", json={
            "name": "Full Test Session",
            "target_url": "https://example.com/admin",
            "cookies": [{"name": "auth", "value": "test123", "domain": "example.com", "path": "/"}],
            "created_by": "test@contractorvault.com",
            "is_active": True
        })
        if resp.status_code in [200, 201]:
            session_id = resp.json()["id"]
            print(f"   ✅ PASS - Session Created: {session_id}")
            results.append(("Session Creation", True))
        else:
            print(f"   ❌ FAIL - Status: {resp.status_code}")
            results.append(("Session Creation", False))
            return results
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        results.append(("Session Creation", False))
        return results

    # ==================== TEST 2: Normal Token Generation ====================
    print("\n[2/6] Testing Normal Token Generation...")
    try:
        resp = httpx.post(f"{API_URL}/sessions/generate-token", json={
            "credential_id": session_id,
            "contractor_email": "normal@test.com",
            "duration_minutes": 60,
            "admin_email": "admin@test.com",
            "is_one_time": False
        })
        if resp.status_code == 200:
            normal_token = resp.json()["claim_url"].split("/")[-1]
            print(f"   ✅ PASS - Token: ...{normal_token[-8:]}")
            results.append(("Normal Token Generation", True))
        else:
            print(f"   ❌ FAIL - Status: {resp.status_code}")
            results.append(("Normal Token Generation", False))
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        results.append(("Normal Token Generation", False))

    # ==================== TEST 3: Burn-on-View Token ====================
    print("\n[3/6] Testing Burn-on-View Token...")
    try:
        resp = httpx.post(f"{API_URL}/sessions/generate-token", json={
            "credential_id": session_id,
            "contractor_email": "burn@test.com",
            "duration_minutes": 60,
            "admin_email": "admin@test.com",
            "is_one_time": True
        })
        if resp.status_code == 200:
            burn_token = resp.json()["claim_url"].split("/")[-1]
            print(f"   ✅ PASS - Burn Token: ...{burn_token[-8:]}")
            results.append(("Burn-on-View Token Generation", True))
        else:
            print(f"   ❌ FAIL - Status: {resp.status_code}")
            results.append(("Burn-on-View Token Generation", False))
            burn_token = None
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        results.append(("Burn-on-View Token Generation", False))
        burn_token = None

    # ==================== TEST 4: Claim Burn Token (1st Use) ====================
    print("\n[4/6] Testing Burn Token Claim (First Use)...")
    if burn_token:
        try:
            resp = httpx.post(f"{API_URL}/sessions/claim/{burn_token}")
            if resp.status_code == 200:
                print(f"   ✅ PASS - Cookies Received")
                results.append(("Burn Token First Claim", True))
            else:
                print(f"   ❌ FAIL - Status: {resp.status_code}")
                results.append(("Burn Token First Claim", False))
        except Exception as e:
            print(f"   ❌ FAIL - Error: {e}")
            results.append(("Burn Token First Claim", False))
    else:
        print("   ⏭️ SKIP - No burn token")
        results.append(("Burn Token First Claim", None))

    # ==================== TEST 5: Burn Token Blocked (2nd Use) ====================
    print("\n[5/6] Testing Burn Token Block (Second Use)...")
    if burn_token:
        try:
            resp = httpx.post(f"{API_URL}/sessions/claim/{burn_token}")
            if resp.status_code == 410:
                print(f"   ✅ PASS - Blocked with 410 Gone")
                results.append(("Burn Token Second Claim Blocked", True))
            else:
                print(f"   ❌ FAIL - Expected 410, got {resp.status_code}")
                results.append(("Burn Token Second Claim Blocked", False))
        except Exception as e:
            print(f"   ❌ FAIL - Error: {e}")
            results.append(("Burn Token Second Claim Blocked", False))
    else:
        print("   ⏭️ SKIP - No burn token")
        results.append(("Burn Token Second Claim Blocked", None))

    # ==================== TEST 6: Kill Switch (Token Revocation) ====================
    print("\n[6/6] Testing Kill Switch (Token Revocation)...")
    try:
        # Generate a token to revoke
        resp = httpx.post(f"{API_URL}/sessions/generate-token", json={
            "credential_id": session_id,
            "contractor_email": "revoke@test.com",
            "duration_minutes": 60,
            "admin_email": "admin@test.com"
        })
        if resp.status_code == 200:
            revoke_token_id = resp.json()["token_id"]
            revoke_token_str = resp.json()["claim_url"].split("/")[-1]
            
            # Revoke it
            revoke_resp = httpx.post(f"{API_URL}/access/revoke/{revoke_token_id}", json={
                "token_id": revoke_token_id,
                "admin_email": "admin@test.com",
                "reason": "Test revocation"
            })
            
            if revoke_resp.status_code == 200:
                # Try to claim revoked token
                claim_resp = httpx.post(f"{API_URL}/sessions/claim/{revoke_token_str}")
                if claim_resp.status_code == 403:
                    print(f"   ✅ PASS - Token revoked and blocked (403)")
                    results.append(("Kill Switch", True))
                else:
                    print(f"   ❌ FAIL - Revoked token not blocked: {claim_resp.status_code}")
                    results.append(("Kill Switch", False))
            else:
                print(f"   ❌ FAIL - Revoke returned: {revoke_resp.status_code}")
                results.append(("Kill Switch", False))
        else:
            print(f"   ❌ FAIL - Token generation failed: {resp.status_code}")
            results.append(("Kill Switch", False))
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        results.append(("Kill Switch", False))

    # ==================== SUMMARY ====================
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)
    
    for name, result in results:
        icon = "✅" if result is True else "❌" if result is False else "⏭️"
        status = "PASS" if result is True else "FAIL" if result is False else "SKIP"
        print(f"   {icon} {name}: {status}")
    
    print("-" * 60)
    print(f"   Total: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    
    if failed == 0:
        print("\n✨ ALL TESTS PASSED! System is fully operational. ✨")
        return 0
    else:
        print(f"\n⚠️ {failed} TEST(S) FAILED. Review above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(test_all())
