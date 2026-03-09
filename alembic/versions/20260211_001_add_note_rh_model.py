"""Add NoteRH model for RH service notes

Revision ID: 20260211_001_add_note_rh
Revises: 20260205_002_magasinier_constraints
Create Date: 2026-02-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = '20260211_001_add_note_rh'
down_revision = '20260205_002_magasinier_constraints'
branch_labels = None
depends_on = None


def upgrade():
    # ### Create note_rh table ###
    # Check if table exists before creating it
    ctx = op.get_context()
    if not ctx.dialect.has_table(ctx.bind, 'note_rh'):
        op.create_table(
            'note_rh',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('titre', sa.String(length=200), nullable=False),
            sa.Column('contenu', sa.Text(), nullable=False),
            sa.Column('author_id', sa.Integer(), nullable=False),
            sa.Column('date_creation', sa.DateTime(), nullable=False),
            sa.Column('date_publication', sa.DateTime(), nullable=True),
            sa.Column('destinataires', sa.String(length=50), nullable=False, server_default='tous'),
            sa.Column('zone_cible', sa.String(length=100), nullable=True),
            sa.Column('service_cible', sa.String(length=50), nullable=True),
            sa.Column('actif', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('date_archivage', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_note_rh_actif'), 'note_rh', ['actif'], unique=False)
    else:
        # Table exists, check if author_id column exists
        columns = ctx.dialect.get_columns(ctx.bind, 'note_rh')
        column_names = [col['name'] for col in columns]
        if 'author_id' not in column_names:
            op.add_column('note_rh', sa.Column('author_id', sa.Integer(), nullable=True))
            op.create_foreign_key(None, 'note_rh', 'user', ['author_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### Drop note_rh table ###
    op.drop_index(op.f('ix_note_rh_actif'), table_name='note_rh')
    op.drop_table('note_rh')
    # ### end Alembic commands ###
