import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

# Parse the URI manually to be safe
# mysql+pymysql://root:@localhost/telcoms
db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
print(f"Connecting to: {db_uri}")

try:
    # Very simple connection
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='telcoms'
    )
    
    with conn.cursor() as cursor:
        print("Checking if column exists...")
        cursor.execute("SHOW COLUMNS FROM user LIKE 'last_login'")
        result = cursor.fetchone()
        
        if not result:
            print("Adding column last_login...")
            cursor.execute("ALTER TABLE user ADD COLUMN last_login DATETIME NULL")
            conn.commit()
            print("Column added successfully!")
        else:
            print("Column last_login already exists.")
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
