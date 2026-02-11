"""
Add form_field_embeddings table for RAG-based field intelligence.

Revision ID: add_form_field_embeddings
Revises: previous migration (auto-detected)
Create Date: 2026-02-02 13:38:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# Try to import pgvector for PostgreSQL, fallback for SQLite
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


# revision identifiers, used by Alembic.
revision = 'add_form_field_embeddings'
down_revision = None  # Will be auto-detected by Alembic
branch_labels = None
depends_on = None


def upgrade():
    """Create form_field_embeddings table."""
    
    # Define embedding column based on database type
    if PGVECTOR_AVAILABLE:
        embedding_column = sa.Column('embedding', Vector(384), nullable=True)
    else:
        # SQLite fallback - store as TEXT (JSON array)
        embedding_column = sa.Column('embedding', sa.Text(), nullable=True)
    
    op.create_table(
        'form_field_embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('program_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('field_label', sa.Text(), nullable=False),
        sa.Column('field_type', sa.String(50), nullable=False),
        sa.Column('successful_value', sa.Text(), nullable=True),
        embedding_column,
        sa.Column('success_count', sa.Integer(), default=0),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('form_context', postgresql.JSONB().with_variant(sa.JSON(), 'sqlite'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for performance
    op.create_index('ix_embeddings_tenant', 'form_field_embeddings', ['tenant_id'])
    op.create_index('ix_embeddings_program', 'form_field_embeddings', ['program_id'])
    op.create_index('ix_embeddings_field_label', 'form_field_embeddings', ['field_label'])
    op.create_index('ix_embeddings_created_at', 'form_field_embeddings', ['created_at'])


def downgrade():
    """Drop form_field_embeddings table."""
    op.drop_index('ix_embeddings_created_at', table_name='form_field_embeddings')
    op.drop_index('ix_embeddings_field_label', table_name='form_field_embeddings')
    op.drop_index('ix_embeddings_program', table_name='form_field_embeddings')
    op.drop_index('ix_embeddings_tenant', table_name='form_field_embeddings')
    op.drop_table('form_field_embeddings')
