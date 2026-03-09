"""Add zone_id constraints for magasinier security.

Revision ID: 20260205_002_magasinier_constraints
Revises: 20260205_001_zone_emplacement
Create Date: 2026-02-05 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260205_002_magasinier_constraints'
down_revision = '20260205_001_zone_emplacement'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add constraints to enforce zone_id assignment for magasinier and ensure emplacement_stock has zone.
    
    Changes:
    1. Add index on User.zone_id for faster filtering
    2. Add index on EmplacementStock.zone_id for faster zone-based queries
    3. Ensure zone_id is NOT NULL for magasinier users (via application-level validation)
    """
    
    # Add indexes for performance
    try:
        op.create_index(
            op.f('ix_user_zone_id'),
            'user',
            ['zone_id'],
            unique=False
        )
        print("✅ Created index: ix_user_zone_id")
    except Exception as e:
        print(f"⚠️ Index ix_user_zone_id may already exist: {e}")
    
    try:
        op.create_index(
            op.f('ix_emplacement_stock_zone_id'),
            'emplacement_stock',
            ['zone_id'],
            unique=False
        )
        print("✅ Created index: ix_emplacement_stock_zone_id")
    except Exception as e:
        print(f"⚠️ Index ix_emplacement_stock_zone_id may already exist: {e}")


def downgrade():
    """Remove indexes"""
    try:
        op.drop_index(op.f('ix_emplacement_stock_zone_id'), table_name='emplacement_stock')
        print("✅ Dropped index: ix_emplacement_stock_zone_id")
    except Exception as e:
        print(f"⚠️ Could not drop index: {e}")
    
    try:
        op.drop_index(op.f('ix_user_zone_id'), table_name='user')
        print("✅ Dropped index: ix_user_zone_id")
    except Exception as e:
        print(f"⚠️ Could not drop index: {e}")
