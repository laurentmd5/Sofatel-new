from app import app, db
from models import User, Produit
from routes.auth import dashboard
from flask import url_for

with app.app_context():
    # Find a magasinier
    user = User.query.filter_by(role='magasinier').first()
    if not user:
        print("No magician found")
        exit()
        
    print(f"Testing for user: {user.username} (Zone: {user.zone_id})")
    
    # We need to simulate a request/session for flask_login
    from flask import Flask, session
    from flask_login import login_user, LoginManager
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    with app.test_request_context():
        login_user(user)
        try:
            from routes.auth import dashboard
            # We can't call it directly easily because it's a route function
            # Let's just run the code inside
            
            from zone_rbac import filter_produit_by_emplacement_zone
            q = Produit.query
            print("Filtering products...")
            results = filter_produit_by_emplacement_zone(q).all()
            print(f"Success! Found {len(results)} products.")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
