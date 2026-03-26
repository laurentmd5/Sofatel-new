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
    
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name
    )
    
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT id, username, email FROM user")
        users = cursor.fetchall()
        with open('all_users_in_db.txt', 'w') as f:
            for u in users:
                f.write(f"{u['id']},{u['username']},{u['email']}\n")
                
    conn.close()
except Exception as e:
    with open('all_users_in_db.txt', 'w') as f:
        f.write(f"Error: {e}\n")
