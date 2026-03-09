import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv('SQLALCHEMY_DATABASE_URI'))

with engine.begin() as conn:
    # Delete the non-existent revision
    conn.execute(text("DELETE FROM alembic_version WHERE version_num = '8d5157421e44'"))
    print('✅ Deleted invalid alembic_version entry')
    
    # Verify
    result = conn.execute(text('SELECT * FROM alembic_version'))
    rows = result.fetchall()
    print('Current alembic_version entries:')
    for row in rows:
        print(f'  {row}')
