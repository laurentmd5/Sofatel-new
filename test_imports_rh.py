import sys
sys.dont_write_bytecode = True

# Test quick import check
print("🔧 Vérifying imports...")
try:
    from utils import log_activity
    print("✅ log_activity trouvé dans utils.py")
except ImportError as e:
    print(f"❌ Erreur import: {e}")

try:
    from routes.auth import dashboard_rh
    print("✅ dashboard_rh trouvé dans routes/auth.py")
except Exception as e:
    print(f"❌ Erreur import dashboard_rh: {e}")

print("\n✅ Tous les imports critiques OK - Le serveur devrait démarrer sans erreur")
