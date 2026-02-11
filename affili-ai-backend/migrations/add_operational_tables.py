"""Add operational governance tables

Revision ID: add_operational_tables
Revises: add_form_field_embeddings
Create Date: 2026-02-02

Adds:
- tenant_runtime_flags (persistent kill-switch)
- llm_usage_log (cost tracking ledger)
- operator_action_log (human intervention audit)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_operational_tables'
down_revision = 'add_form_field_embeddings'  # Adjust if needed
branch_labels = None
depends_on = None


def upgrade():
    # Create tenant_runtime_flags table
    op.create_table(
        'tenant_runtime_flags',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ai_disabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('disable_reason', sa.Text(), nullable=True),
        sa.Column('disabled_at', sa.DateTime(), nullable=True),
        sa.Column('disabled_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['disabled_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('tenant_id')
    )
    op.create_index('ix_tenant_runtime_flags_ai_disabled', 'tenant_runtime_flags', ['ai_disabled'])
    
    # Create llm_usage_log table
    op.create_table(
        'llm_usage_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Numeric(10, 6), nullable=False),
        sa.Column('operation', sa.String(50), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_llm_usage_log_tenant_id', 'llm_usage_log', ['tenant_id'])
    op.create_index('ix_llm_usage_log_task_id', 'llm_usage_log', ['task_id'])
    op.create_index('ix_llm_usage_log_created_at', 'llm_usage_log', ['created_at'])
    op.create_index('ix_llm_usage_tenant_created', 'llm_usage_log', ['tenant_id', 'created_at'])
    
    # Create operator_action_log table
    op.create_table(
        'operator_action_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('operator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.Enum('RESUME_TASK', 'CANCEL_TASK', 'MANUAL_OVERRIDE', 'FEEDBACK_SUBMITTED', 
                                     'KILLSWITCH_ENABLED', 'KILLSWITCH_DISABLED', 'QUOTA_ADJUSTED', 
                                     name='operatoractiontype'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_operator_action_log_tenant_id', 'operator_action_log', ['tenant_id'])
    op.create_index('ix_operator_action_log_operator_id', 'operator_action_log', ['operator_id'])
    op.create_index('ix_operator_action_log_task_id', 'operator_action_log', ['task_id'])
    op.create_index('ix_operator_action_log_action', 'operator_action_log', ['action'])
    op.create_index('ix_operator_action_log_created_at', 'operator_action_log', ['created_at'])


def downgrade():
    op.drop_table('operator_action_log')
    op.drop_table('llm_usage_log')
    op.drop_table('tenant_runtime_flags')
    op.execute('DROP TYPE operatoractiontype')
