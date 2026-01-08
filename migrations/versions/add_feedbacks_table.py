"""add feedbacks table

Revision ID: add_feedbacks_table
Revises: 
Create Date: 2025-12-29 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_feedbacks_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'feedbacks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('booking_id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('agency_id', sa.String(length=36), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('feedbacks')
