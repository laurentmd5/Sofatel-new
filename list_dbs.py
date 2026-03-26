import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv('SQLALCHEMY_DATABASE_URI')
try:
    auth_part = uri.split('//')[1].split('@')[0]
    host_part = uri.split('@')[1].split('/')[0]
    
    user = auth_part.split(':')[0]
    password = auth_part.split(':')[1] if ':' in auth_part else ''
    
    host = host_part.split(':')[0]
    port = int(host_part.split(':')[1]) if ':' in host_part else 3306
    
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password
    )
    
    with conn.cursor() as cursor:
        cursor.execute("SHOW DATABASES")
        dbs = cursor.fetchall()
        with open('databases.txt', 'w') as f:
            for db in dbs:
                f.write(f"{db[0]}\n")
                
    conn.close()
except Exception as e:
    with open('databases.txt', 'w') as f:
        f.write(f"Error: {e}\n")
