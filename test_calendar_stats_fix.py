#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for calendar and stats API response format
Vérifie que les réponses incluent le champ 'success': True
"""

import json
import requests
from datetime import datetime
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"

# Test login first
print("[LOGIN] Connexion...")
login_response = requests.post(f"{BASE_URL}/login", data={
    'username': 'admin',
    'password': 'admin'
}, allow_redirects=True)
session = requests.Session()
session.cookies.update(requests.cookies.RequestsCookieJar())

# Get session cookies
for cookie in login_response.cookies:
    session.cookies.set_cookie(cookie)

print("\n" + "="*60)
print("TEST 1: GET /api/rh/calendar/team")
print("="*60)

year = datetime.now().year
month = datetime.now().month
params = {'year': year, 'month': month}

try:
    resp = session.get(f"{BASE_URL}/api/rh/calendar/team", params=params)
    print(f"Status: {resp.status_code}")
    
    data = resp.json()
    print(f"\nReponse structure:")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    
    # Check required fields
    required_fields = ['success', 'year', 'month', 'calendar']
    missing = [f for f in required_fields if f not in data]
    
    if missing:
        print(f"\n❌ MISSING FIELDS: {missing}")
    else:
        print(f"\n✅ All required fields present: {required_fields}")
    
    # Check success value
    if data.get('success') is True:
        print("✅ success = True")
    else:
        print(f"❌ success = {data.get('success')} (should be True)")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("Test 2: GET /api/rh/leave/stats")
print("="*60)

try:
    resp = session.get(f"{BASE_URL}/api/rh/leave/stats", params={'year': year})
    print(f"Status: {resp.status_code}")
    
    data = resp.json()
    print(f"\nReponse structure:")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    
    # Check required fields
    required_fields = ['success', 'year', 'total', 'approved', 'pending', 'rejected', 'by_technicien']
    missing = [f for f in required_fields if f not in data]
    
    if missing:
        print(f"\n❌ MISSING FIELDS: {missing}")
    else:
        print(f"\n✅ All required fields present: {required_fields}")
    
    # Check success value
    if data.get('success') is True:
        print("✅ success = True")
    else:
        print(f"❌ success = {data.get('success')} (should be True)")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("✅ TESTS COMPLETE")
print("="*60)
