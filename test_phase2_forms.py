#!/usr/bin/env python3
"""Test PHASE 2 Forms - Verify magasinier-specific forms created"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

print("=" * 80)
print("🧪 PHASE 2 FORMS TESTING")
print("=" * 80)

# TEST 1: Check forms.py has magasinier forms
print("\n[TEST 1] 🔍 Magasinier Forms in forms.py")
print("-" * 80)

with open('forms.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
    has_create_mag_form = 'class CreateUserMagasinierForm' in content
    has_entree_mag_form = 'class EntreeStockFormMagasinier' in content
    has_sortie_mag_form = 'class SortieStockFormMagasinier' in content
    
    print(f"CreateUserMagasinierForm: {'✅' if has_create_mag_form else '❌'}")
    print(f"EntreeStockFormMagasinier: {'✅' if has_entree_mag_form else '❌'}")
    print(f"SortieStockFormMagasinier: {'✅' if has_sortie_mag_form else '❌'}")
    
    has_zone_validation = 'zone_id != self.magasinier_zone_id' in content
    has_zone_filtering = 'filter_by(zone_id=magasinier_zone_id' in content
    
    print(f"Zone validation in forms: {'✅' if has_zone_validation else '❌'}")
    print(f"Zone filtering in forms: {'✅' if has_zone_filtering else '❌'}")

# TEST 2: Import forms to verify syntax
print("\n[TEST 2] 🔍 Forms Import Test")
print("-" * 80)

try:
    from forms import (
        CreateUserMagasinierForm, 
        EntreeStockFormMagasinier,
        SortieStockFormMagasinier
    )
    print("✅ All magasinier forms imported successfully")
    print(f"  - CreateUserMagasinierForm: {CreateUserMagasinierForm.__doc__}")
    print(f"  - EntreeStockFormMagasinier: {EntreeStockFormMagasinier.__doc__}")
    print(f"  - SortieStockFormMagasinier: {SortieStockFormMagasinier.__doc__}")
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"⚠️ Error: {e}")

# TEST 3: Check zone field validation
print("\n[TEST 3] 🔍 Zone Field Configuration")
print("-" * 80)

try:
    form = CreateUserMagasinierForm()
    print(f"Zone field label: {form.zone.label.text}")
    print(f"Zone validators: {form.zone.validators}")
    
    # Check that zone is DataRequired for magasinier
    has_required_validator = any(
        str(validator).find('DataRequired') >= 0 
        for validator in form.zone.validators
    )
    print(f"Zone field is DataRequired: {'✅' if has_required_validator else '❌'}")
    
except Exception as e:
    print(f"⚠️ Error creating form: {e}")

# TEST 4: Verify forms are documented
print("\n[TEST 4] 🔍 Forms Documentation")
print("-" * 80)

if has_create_mag_form:
    start = content.find('class CreateUserMagasinierForm')
    snippet = content[start:start+500]
    has_doc = '"""' in snippet or "'''" in snippet
    print(f"CreateUserMagasinierForm documented: {'✅' if has_doc else '⚠️'}")

if has_entree_mag_form:
    start = content.find('class EntreeStockFormMagasinier')
    snippet = content[start:start+500]
    has_doc = '"""' in snippet or "'''" in snippet
    print(f"EntreeStockFormMagasinier documented: {'✅' if has_doc else '⚠️'}")

if has_sortie_mag_form:
    start = content.find('class SortieStockFormMagasinier')
    snippet = content[start:start+500]
    has_doc = '"""' in snippet or "'''" in snippet
    print(f"SortieStockFormMagasinier documented: {'✅' if has_doc else '⚠️'}")

# FINAL SUMMARY
print("\n" + "=" * 80)
print("📊 PHASE 2 FORMS TEST SUMMARY")
print("=" * 80)

checks = [
    ('CreateUserMagasinierForm exists', has_create_mag_form),
    ('EntreeStockFormMagasinier exists', has_entree_mag_form),
    ('SortieStockFormMagasinier exists', has_sortie_mag_form),
    ('Zone validation present', has_zone_validation),
    ('Zone filtering present', has_zone_filtering),
]

passed = sum(1 for _, result in checks if result)
total = len(checks)

for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"{status} {check_name}")

print("\n" + "=" * 80)
if passed == total:
    print(f"✅ ALL FORMS CREATED SUCCESSFULLY ({passed}/{total})")
    print("✅ PHASE 2.1-2.3 (Forms) READY FOR TEMPLATE INTEGRATION")
else:
    print(f"⚠️  {passed}/{total} checks passed")
print("=" * 80)
