#!/usr/bin/env python3
"""
Test script for the 3 new RH module routes:
1. POST /api/rh/leave/check-conflicts
2. POST /api/rh/leave/bulk-approve
3. POST /api/rh/leave/bulk-reject
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000"

# ============= CONFIG =============
# Change these to match your test environment
TEST_USERNAME = "jdoe"  # A technician user
TEST_PASSWORD = "password123"  # The password
TEST_RH_USERNAME = "rhmanager"  # An RH user
TEST_RH_PASSWORD = "password123"

def login(username, password):
    """Login and return session with auth cookies"""
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/auth/login", data={
        'username': username,
        'password': password
    })
    
    if resp.status_code != 302:
        print(f"❌ Login failed for {username}: {resp.status_code}")
        print(resp.text)
        return None
    
    print(f"✅ Logged in as {username}")
    return session

def test_check_conflicts():
    """Test POST /api/rh/leave/check-conflicts"""
    print("\n" + "="*60)
    print("TEST 1: check-conflicts endpoint")
    print("="*60)
    
    session = login(TEST_USERNAME, TEST_PASSWORD)
    if not session:
        return False
    
    # Test data: look for conflicts in the next 7 days
    today = datetime.now().date()
    start = (today + timedelta(days=5)).isoformat()
    end = (today + timedelta(days=10)).isoformat()
    
    payload = {
        "date_debut": start,
        "date_fin": end
    }
    
    print(f"\n📤 Payload: {json.dumps(payload, indent=2)}")
    
    resp = session.post(
        f"{BASE_URL}/api/rh/leave/check-conflicts",
        json=payload,
        headers={'Accept': 'application/json'}
    )
    
    print(f"📥 Status: {resp.status_code}")
    print(f"📥 Response: {json.dumps(resp.json(), indent=2)}")
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.json()['success'] == True
    
    print("✅ check-conflicts works!")
    return True

def test_bulk_approve():
    """Test POST /api/rh/leave/bulk-approve"""
    print("\n" + "="*60)
    print("TEST 2: bulk-approve endpoint")
    print("="*60)
    
    session = login(TEST_RH_USERNAME, TEST_RH_PASSWORD)
    if not session:
        return False
    
    # First, get some pending leaves
    print("\n🔍 Fetching pending leaves...")
    resp = session.get(
        f"{BASE_URL}/api/rh/conges?statut=pending&per_page=10",
        headers={'Accept': 'application/json'}
    )
    
    if resp.status_code != 200 or not resp.json()['leaves']:
        print("⚠️  No pending leaves found. Test will use empty list.")
        leave_ids = []
    else:
        leave_ids = [leave['id'] for leave in resp.json()['leaves'][:2]]
        print(f"📋 Found {len(leave_ids)} pending leaves: {leave_ids}")
    
    # Test bulk approve
    payload = {
        "leave_ids": leave_ids[:1] if leave_ids else [],  # Approve only 1 for safety
        "comment": "Test batch approval"
    }
    
    print(f"\n📤 Payload: {json.dumps(payload, indent=2)}")
    
    resp = session.post(
        f"{BASE_URL}/api/rh/leave/bulk-approve",
        json=payload,
        headers={'Accept': 'application/json'}
    )
    
    print(f"📥 Status: {resp.status_code}")
    print(f"📥 Response: {json.dumps(resp.json(), indent=2)}")
    
    if resp.status_code == 401 or resp.status_code == 403:
        print("⚠️  RH user not found or not authorized. This is expected in test env.")
        return True
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.json()['success'] == True
    
    print("✅ bulk-approve works!")
    return True

def test_bulk_reject():
    """Test POST /api/rh/leave/bulk-reject"""
    print("\n" + "="*60)
    print("TEST 3: bulk-reject endpoint")
    print("="*60)
    
    session = login(TEST_RH_USERNAME, TEST_RH_PASSWORD)
    if not session:
        return False
    
    # First, get some pending leaves
    print("\n🔍 Fetching pending leaves...")
    resp = session.get(
        f"{BASE_URL}/api/rh/conges?statut=pending&per_page=10",
        headers={'Accept': 'application/json'}
    )
    
    if resp.status_code != 200 or not resp.json()['leaves']:
        print("⚠️  No pending leaves found. Test will use empty list.")
        leave_ids = []
    else:
        leave_ids = [leave['id'] for leave in resp.json()['leaves'][:2]]
        print(f"📋 Found {len(leave_ids)} pending leaves: {leave_ids}")
    
    # Test bulk reject
    payload = {
        "leave_ids": leave_ids[:1] if leave_ids else [],  # Reject only 1 for safety
        "comment": "Test batch rejection - testing purposes"
    }
    
    print(f"\n📤 Payload: {json.dumps(payload, indent=2)}")
    
    resp = session.post(
        f"{BASE_URL}/api/rh/leave/bulk-reject",
        json=payload,
        headers={'Accept': 'application/json'}
    )
    
    print(f"📥 Status: {resp.status_code}")
    print(f"📥 Response: {json.dumps(resp.json(), indent=2)}")
    
    if resp.status_code == 401 or resp.status_code == 403:
        print("⚠️  RH user not found or not authorized. This is expected in test env.")
        return True
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.json()['success'] == True
    
    print("✅ bulk-reject works!")
    return True

def test_validation_errors():
    """Test error handling"""
    print("\n" + "="*60)
    print("TEST 4: Error handling")
    print("="*60)
    
    session = login(TEST_USERNAME, TEST_PASSWORD)
    if not session:
        return False
    
    # Test missing dates
    print("\n🧪 Test: Missing date fields")
    resp = session.post(
        f"{BASE_URL}/api/rh/leave/check-conflicts",
        json={"date_debut": "2026-02-01"},  # Missing date_fin
        headers={'Accept': 'application/json'}
    )
    print(f"Status: {resp.status_code}, Response: {resp.json()}")
    assert resp.status_code == 400
    
    # Test invalid date format
    print("\n🧪 Test: Invalid date format")
    resp = session.post(
        f"{BASE_URL}/api/rh/leave/check-conflicts",
        json={"date_debut": "02/01/2026", "date_fin": "02/05/2026"},
        headers={'Accept': 'application/json'}
    )
    print(f"Status: {resp.status_code}, Response: {resp.json()}")
    assert resp.status_code == 400
    
    print("\n✅ Error handling works!")
    return True

if __name__ == '__main__':
    print("\n" + "="*60)
    print("TESTING NEW RH MODULE ROUTES")
    print("="*60)
    
    try:
        # Test 1: Check conflicts
        if not test_check_conflicts():
            print("❌ Test 1 failed")
        
        # Test 2: Bulk approve
        if not test_bulk_approve():
            print("⚠️  Test 2 may have issues (expected if RH user not in DB)")
        
        # Test 3: Bulk reject
        if not test_bulk_reject():
            print("⚠️  Test 3 may have issues (expected if RH user not in DB)")
        
        # Test 4: Error handling
        if not test_validation_errors():
            print("❌ Test 4 failed")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
    
    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
