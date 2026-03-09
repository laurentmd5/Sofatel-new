#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for calendar and stats API response format
"""

import json
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

session = requests.Session()

year = datetime.now().year
month = datetime.now().month
params = {'year': year, 'month': month}

print("\n=== TEST 1: /api/rh/calendar/team ===\n")

try:
    resp = requests.get(f"{BASE_URL}/api/rh/calendar/team", params=params)
    print(f"Status: {resp.status_code}")
    
    data = resp.json()
    
    # Check required fields
    required = ['success', 'year', 'month', 'calendar']
    for field in required:
        if field in data:
            print(f"  [OK] Field '{field}' present")
        else:
            print(f"  [ERROR] Field '{field}' MISSING")
    
    # Check success value
    success = data.get('success')
    if success is True:
        print(f"  [OK] success = True")
        if isinstance(data.get('calendar'), dict):
            print(f"  [OK] calendar is a dict with {len(data['calendar'])} dates")
    else:
        print(f"  [ERROR] success = {success}")
        
except Exception as e:
    print(f"[ERROR] {e}")

print("\n=== TEST 2: /api/rh/leave/stats ===\n")

try:
    resp = requests.get(f"{BASE_URL}/api/rh/leave/stats", params={'year': year})
    print(f"Status: {resp.status_code}")
    
    data = resp.json()
    
    # Check required fields
    required = ['success', 'year', 'total', 'approved', 'pending', 'rejected', 'by_technicien']
    for field in required:
        if field in data:
            print(f"  [OK] Field '{field}' present")
        else:
            print(f"  [ERROR] Field '{field}' MISSING")
    
    # Check success value
    success = data.get('success')
    if success is True:
        print(f"  [OK] success = True")
        print(f"  [OK] Total: {data.get('total')}, Approved: {data.get('approved')}")
    else:
        print(f"  [ERROR] success = {success}")
        
except Exception as e:
    print(f"[ERROR] {e}")

print("\n=== TESTS COMPLETE ===\n")
