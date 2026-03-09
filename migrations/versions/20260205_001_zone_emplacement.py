"""Add zone_id to emplacement_stock

Revision ID: 20260205_001_zone_emplacement
Revises: 8d5157421e44
Create Date: 2026-02-05 10:00:00.000000

This migration adds the zone_id foreign key to emplacement_stock table
to support zone-based filtering for magasinier users.

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260205_001_zone_emplacement'
down_revision = '8d5157421e44'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add zone_id column to emplacement_stock"""
    # Add zone_id column
    op.add_column(
        'emplacement_stock',
        sa.Column('zone_id', sa.Integer(), nullable=True)
    )
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_emplacement_stock_zone_id',
        'emplacement_stock',
        'zone',
        ['zone_id'],
        ['id']
    )
    
    # Create index for performance
    op.create_index(
        'idx_emplacement_stock_zone_id',
        'emplacement_stock',
        ['zone_id']
    )


def downgrade() -> None:
    """Remove zone_id column from emplacement_stock"""
    # Drop index
    op.drop_index('idx_emplacement_stock_zone_id', table_name='emplacement_stock')
    
    # Drop foreign key
    op.drop_constraint(
        'fk_emplacement_stock_zone_id',
        'emplacement_stock',
        type_='foreignkey'
    )
    
    # Drop column
    op.drop_column('emplacement_stock', 'zone_id')
