"""Revision to add role column to users table

Revision ID: add_user_role_column
Revises: 8b3b5867d2ac
Create Date: 2026-02-11 11:34:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_role_column'
down_revision = '8b3b5867d2ac'
branch_labels = None
depends_on = None


def upgrade():
    # Add role column with default OPERATOR
    op.add_column('users', sa.Column('role', sa.String(length=50), nullable=False, server_default='OPERATOR'))
    
    # Create index for efficient role-based queries
    op.create_index('ix_users_role', 'users', ['role'])


def downgrade():
    op.drop_index('ix_users_role', table_name='users')
    op.drop_column('users', 'role')
