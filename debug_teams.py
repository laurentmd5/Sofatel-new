import pymysql
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('SQLALCHEMY_DATABASE_URI')
db_name = uri.split('/')[-1]
auth_part = uri.split('//')[1].split('@')[0]
user = auth_part.split(':')[0]
password = auth_part.split(':')[1] if ':' in auth_part else ''
host_part = uri.split('@')[1].split('/')[0]
host = host_part.split(':')[0]

conn = pymysql.connect(host=host, user=user, password=password, database=db_name)
with conn.cursor(pymysql.cursors.DictCursor) as cursor:
    cursor.execute("SELECT id, nom_equipe, date_publication, publie FROM equipe WHERE actif=1")
    equipes = cursor.fetchall()
    with open('debug_teams_out.txt', 'w') as f:
        f.write(f"--- Teams at {date.today()} ---\n")
        for e in equipes:
            f.write(f"{e['id']} | {e['nom_equipe']} | Pub: {e['publie']} | Date: {e['date_publication']}\n")
conn.close()
