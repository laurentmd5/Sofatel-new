import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

load_dotenv()
engine = create_engine(os.getenv('SQLALCHEMY_DATABASE_URI'))
inspector = inspect(engine)

# Check indexes on user table
user_indexes = inspector.get_indexes('user')
print('✅ Indexes on user table:')
for idx in user_indexes:
    print(f'  - {idx["name"]}: {idx["column_names"]}')

# Check indexes on emplacement_stock table
emplacement_indexes = inspector.get_indexes('emplacement_stock')
print('\n✅ Indexes on emplacement_stock table:')
for idx in emplacement_indexes:
    print(f'  - {idx["name"]}: {idx["column_names"]}')

# Check alembic_version
print('\n✅ Current migration status:')
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT * FROM alembic_version'))
    for row in result:
        print(f'  - Applied: {row[0]}')
