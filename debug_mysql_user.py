import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv('SQLALCHEMY_DATABASE_URI')
# mysql+pymysql://root:@localhost/telcoms
# extract host, user, password, db
try:
    auth_part = uri.split('//')[1].split('@')[0]
    host_part = uri.split('@')[1].split('/')[0]
    db_name = uri.split('/')[-1]
    
    user = auth_part.split(':')[0]
    password = auth_part.split(':')[1] if ':' in auth_part else ''
    
    host = host_part.split(':')[0]
    port = int(host_part.split(':')[1]) if ':' in host_part else 3306
    
    print(f"Connecting to {host}:{port}, DB: {db_name}, User: {user}")
    
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name
    )
    
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        username = 'adiallo'
        email = 'alassane.diallo@sofatelcom.com'
        
        print(f"\nChecking for username='{username}' or email='{email}'")
        cursor.execute("SELECT id, username, email, role, actif FROM user WHERE username = %s OR email = %s", (username, email))
        results = cursor.fetchall()
        
        if results:
            print(f"Found {len(results)} matching user(s):")
            for row in results:
                print(row)
        else:
            print("No matching user found.")
            
        print("\nChecking for any users with 'diallo' in username or email:")
        cursor.execute("SELECT id, username, email FROM user WHERE username LIKE '%diallo%' OR email LIKE '%diallo%'")
        results = cursor.fetchall()
        for row in results:
            print(row)
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
