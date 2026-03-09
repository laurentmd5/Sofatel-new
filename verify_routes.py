#!/usr/bin/env python3
"""
Quick test: Verify that the 3 new routes are properly registered in Flask
"""
import sys
sys.path.insert(0, '/Users/Lenovo/Downloads/SOFATELCOM')

from flask import Flask
from routes.rh import rh_bp

app = Flask(__name__)
app.register_blueprint(rh_bp, url_prefix='/api/rh')

print("\n" + "="*60)
print("CHECKING REGISTERED ROUTES")
print("="*60)

# Get all registered routes
routes = []
for rule in app.url_map.iter_rules():
    if 'rh' in rule.rule:
        routes.append({
            'rule': rule.rule,
            'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
            'endpoint': rule.endpoint
        })

# Sort for readability
routes.sort(key=lambda x: x['rule'])

print("\n✅ Found RH routes:")
for route in routes:
    print(f"\n  {route['rule']}")
    print(f"    Methods: {route['methods']}")
    print(f"    Endpoint: {route['endpoint']}")

# Check for our 3 new routes
required_routes = [
    ('/api/rh/leave/check-conflicts', ['POST']),
    ('/api/rh/leave/bulk-approve', ['POST']),
    ('/api/rh/leave/bulk-reject', ['POST'])
]

print("\n" + "-"*60)
print("VALIDATION: New routes")
print("-"*60)

all_found = True
for required_path, required_methods in required_routes:
    found = False
    for route in routes:
        if route['rule'] == required_path:
            # Check methods
            for method in required_methods:
                if method in route['methods']:
                    print(f"✅ {required_path} ({method})")
                    found = True
                else:
                    print(f"❌ {required_path} - Missing method {method}")
                    all_found = False
            break
    
    if not found:
        print(f"❌ {required_path} - NOT FOUND")
        all_found = False

print("\n" + "="*60)
if all_found:
    print("✅ ALL REQUIRED ROUTES PRESENT!")
    sys.exit(0)
else:
    print("❌ SOME ROUTES ARE MISSING!")
    sys.exit(1)
print("="*60)
