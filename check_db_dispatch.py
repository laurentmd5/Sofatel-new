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
today = date.today().strftime('%Y-%m-%d')

with conn.cursor(pymysql.cursors.DictCursor) as cursor:
    print(f"--- DB Diagnostic {today} ---")
    
    # Check published teams
    cursor.execute("SELECT id, nom_equipe, zone, service FROM equipe WHERE publie=1 AND date_publication=%s", (today,))
    equipes = cursor.fetchall()
    print(f"Equipes publiées aujourd'hui: {len(equipes)}")
    for e in equipes:
        print(f" - {e['nom_equipe']} | Zone: {e['zone']} | Service: {e['service']}")

    # Check pending demands
    cursor.execute("SELECT id, nd, zone, service FROM demande_intervention WHERE statut IN ('nouveau', 'a_reaffecter')")
    demandes = cursor.fetchall()
    print(f"Demandes en attente: {len(demandes)}")
    for d in demandes[:3]:
        print(f" - {d['nd']} | Zone: {d['zone']} | Service: {d['service']}")

conn.close()
