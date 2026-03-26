from app import app, db
from models import User

with app.app_context():
    username = 'adiallo'
    email = 'alassane.diallo@sofatelcom.com'
    
    user_by_username = User.query.filter_by(username=username).first()
    user_by_email = User.query.filter_by(email=email).first()
    
    print(f"Checking for username: {username}")
    if user_by_username:
        print(f"Found user by username: ID={user_by_username.id}, Username={user_by_username.username}, Email={user_by_username.email}, Actif={user_by_username.actif}")
    else:
        print("No user found by username.")
        
    print(f"\nChecking for email: {email}")
    if user_by_email:
        print(f"Found user by email: ID={user_by_email.id}, Username={user_by_email.username}, Email={user_by_email.email}, Actif={user_by_email.actif}")
    else:
        print("No user found by email.")

    # Show all users to be sure
    print("\nListing all users (first 10):")
    all_users = User.query.limit(10).all()
    for u in all_users:
        print(f"ID={u.id}, Username={u.username}, Email={u.email}")
