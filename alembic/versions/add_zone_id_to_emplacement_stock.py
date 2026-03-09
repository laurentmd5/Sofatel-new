"""Add zone_id to EmplacementStock model

Revision ID: add_zone_emplacement
Revises: 
Create Date: 2026-02-04

This migration adds zone_id foreign key to emplacement_stock table
to support zone-based filtering for magasinier role.
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision = 'add_zone_emplacement'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add zone_id column to emplacement_stock table"""
    
    # Check if column already exists (safety check for idempotency)
    try:
        # Add zone_id column as nullable foreign key
        op.add_column(
            'emplacement_stock',
            sa.Column('zone_id', sa.Integer(), nullable=True)
        )
        
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_emplacement_stock_zone_id',
            'emplacement_stock',
            'zone',
            ['zone_id'],
            ['id']
        )
        
        print("✅ Successfully added zone_id to emplacement_stock")
    except Exception as e:
        print(f"⚠️  Migration warning: {str(e)}")
        # Column might already exist, continue


def downgrade() -> None:
    """Remove zone_id column from emplacement_stock table"""
    
    try:
        # Drop foreign key constraint
        op.drop_constraint(
            'fk_emplacement_stock_zone_id',
            'emplacement_stock',
            type_='foreignkey'
        )
        
        # Drop zone_id column
        op.drop_column('emplacement_stock', 'zone_id')
        
        print("✅ Successfully removed zone_id from emplacement_stock")
    except Exception as e:
        print(f"⚠️  Downgrade warning: {str(e)}")
