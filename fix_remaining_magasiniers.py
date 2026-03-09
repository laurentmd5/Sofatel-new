import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv('SQLALCHEMY_DATABASE_URI'))

# Find and assign zone to magasiniers without zone
with engine.begin() as conn:
    # Find magasiniers without zone
    result = conn.execute(text("""
        SELECT id, username FROM user 
        WHERE role = 'magasinier' AND zone_id IS NULL
        LIMIT 10
    """))
    
    orphans = result.fetchall()
    print(f"Found {len(orphans)} magasiniers without zone:")
    for user_id, username in orphans:
        print(f"  - {username} (ID: {user_id})")
    
    # Assign zone 3 (Dakar) to all orphans
    if orphans:
        conn.execute(text("""
            UPDATE user 
            SET zone_id = 3 
            WHERE role = 'magasinier' AND zone_id IS NULL
        """))
        print(f"\n✅ Assigned zone_id = 3 (Dakar) to {len(orphans)} magasiniers")
        
        # Verify
        result = conn.execute(text("""
            SELECT COUNT(*) FROM user 
            WHERE role = 'magasinier' AND zone_id IS NOT NULL
        """))
        count_with_zone = result.scalar()
        print(f"✅ Total magasiniers with zone: {count_with_zone}")
