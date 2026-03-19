from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Check if column already exists
        result = db.session.execute(text("SHOW COLUMNS FROM user LIKE 'last_login'"))
        if not result.fetchone():
            db.session.execute(text("ALTER TABLE user ADD COLUMN last_login DATETIME"))
            db.session.commit()
            print("Successfully added last_login column to user table.")
        else:
            print("Column last_login already exists.")
    except Exception as e:
        print(f"Error: {e}")
