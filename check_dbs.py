import pymysql

dbs_to_check = ['telcoms', 'qirm8908_sofatel-sn', 'sofatelcom']

for db_name in dbs_to_check:
    try:
        conn = pymysql.connect(
            host='localhost', 
            user='root', 
            password='', 
            database=db_name,
            connect_timeout=2
        )
        print(f"FOUND: {db_name}")
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'user'")
            if cursor.fetchone():
                print(f"  - Table 'user' exists in {db_name}")
                cursor.execute("SHOW COLUMNS FROM user LIKE 'last_login'")
                if cursor.fetchone():
                    print(f"  - Column 'last_login' ALREADY EXISTS in {db_name}")
                else:
                    print(f"  - Column 'last_login' MISSING in {db_name}")
            else:
                print(f"  - Table 'user' NOT FOUND in {db_name}")
        conn.close()
    except Exception as e:
        print(f"NOT FOUND or ERROR for {db_name}: {e}")
