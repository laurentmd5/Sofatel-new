import pymysql
import os

try:
    conn = pymysql.connect(
        host='localhost', 
        user='root', 
        password='', 
        database='telcoms',
        connect_timeout=10
    )
    with conn.cursor() as cursor:
        try:
            print("Attempting to add last_login column...")
            cursor.execute("ALTER TABLE user ADD COLUMN last_login DATETIME NULL")
            conn.commit()
            print("SUCCESS: last_login column added.")
        except pymysql.err.InternalError as e:
            if e.args[0] == 1060: # Duplicate column name
                print("INFO: last_login column already exists.")
            else:
                print(f"MYSQL ERROR: {e}")
        except Exception as e:
            print(f"ERROR: {e}")
    conn.close()
except Exception as e:
    print(f"CONNECTION ERROR: {e}")
