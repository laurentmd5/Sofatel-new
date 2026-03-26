import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv('SQLALCHEMY_DATABASE_URI')
try:
    auth_part = uri.split('//')[1].split('@')[0]
    host_part = uri.split('@')[1].split('/')[0]
    db_name = uri.split('/')[-1]
    
    user = auth_part.split(':')[0]
    password = auth_part.split(':')[1] if ':' in auth_part else ''
    
    host = host_part.split(':')[0]
    port = int(host_part.split(':')[1]) if ':' in host_part else 3306
    
    with open('debug_output.txt', 'w') as f:
        f.write(f"Connecting to {host}:{port}, DB: {db_name}, User: {user}\n")
        
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
            
            f.write(f"\nChecking for username='{username}' or email='{email}'\n")
            cursor.execute("SELECT id, username, email, role, actif FROM user WHERE username = %s OR email = %s", (username, email))
            results = cursor.fetchall()
            
            if results:
                f.write(f"Found {len(results)} matching user(s):\n")
                for row in results:
                    f.write(f"{row}\n")
            else:
                f.write("No matching user found.\n")
                
            f.write("\nChecking for any users with 'diallo' in username or email:\n")
            cursor.execute("SELECT id, username, email FROM user WHERE username LIKE '%diallo%' OR email LIKE '%diallo%'")
            results = cursor.fetchall()
            for row in results:
                f.write(f"{row}\n")
                
        conn.close()
        f.write("\nDONE\n")
except Exception as e:
    with open('debug_output.txt', 'w') as f:
        f.write(f"Error: {e}\n")
