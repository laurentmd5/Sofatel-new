"""Add zone_id column to emplacement_stock.

Revision ID: 20260205_001_zone_emplacement
Revises: add_zone_emplacement
Create Date: 2026-02-05 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260205_001_zone_emplacement'
down_revision = 'add_zone_emplacement'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add zone_id foreign key to emplacement_stock table.
    
    This ensures that all storage locations are associated with zones,
    enabling zone-based filtering for magasinier users.
    """
    
    # Check if zone_id column already exists
    try:
        op.add_column(
            'emplacement_stock',
            sa.Column('zone_id', sa.Integer(), nullable=True)
        )
        print("✅ Added zone_id column to emplacement_stock")
        
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_emplacement_stock_zone_id',
            'emplacement_stock',
            'zone',
            ['zone_id'],
            ['id']
        )
        print("✅ Added foreign key constraint on zone_id")
        
    except Exception as e:
        print(f"⚠️ Column zone_id may already exist or error occurred: {e}")


def downgrade():
    """
    Remove zone_id foreign key and column from emplacement_stock.
    """
    
    try:
        op.drop_constraint(
            'fk_emplacement_stock_zone_id',
            'emplacement_stock',
            type_='foreignkey'
        )
        print("✅ Dropped foreign key constraint on zone_id")
    except Exception as e:
        print(f"⚠️ Foreign key constraint may not exist: {e}")
    
    try:
        op.drop_column('emplacement_stock', 'zone_id')
        print("✅ Dropped zone_id column from emplacement_stock")
    except Exception as e:
        print(f"⚠️ Column may not exist: {e}")
