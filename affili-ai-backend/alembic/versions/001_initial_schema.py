"""Initial schema with program, application, task, credential, response_pool

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create program table
    op.create_table(
        'program',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('affiliate_url', sa.String(length=500), nullable=True),
        sa.Column('commission_rate', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_ok=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_program_name'), 'program', ['name'], unique=True)
    op.create_index(op.f('ix_program_created_at'), 'program', ['created_at'])

    # Create application table
    op.create_table(
        'application',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('program_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('application_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(length=500), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_ok=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['program_id'], ['program.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_application_program_id'), 'application', ['program_id'])
    op.create_index(op.f('ix_application_status'), 'application', ['status'])
    op.create_index(op.f('ix_application_created_at'), 'application', ['created_at'])

    # Create task table
    op.create_table(
        'task',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('target_url', sa.String(length=500), nullable=True),
        sa.Column('screenshot_path', sa.String(length=500), nullable=True),
        sa.Column('agent_id', sa.String(length=100), nullable=True),
        sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_log', postgresql.JSON(astext_ok=True), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_ok=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['application.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_application_id'), 'task', ['application_id'])
    op.create_index(op.f('ix_task_status'), 'task', ['status'])
    op.create_index(op.f('ix_task_agent_id'), 'task', ['agent_id'])
    op.create_index(op.f('ix_task_created_at'), 'task', ['created_at'])

    # Create credential table
    op.create_table(
        'credential',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('encrypted_value', sa.Text(), nullable=False),
        sa.Column('meta_data', postgresql.JSON(astext_ok=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credential_name'), 'credential', ['name'], unique=True)
    op.create_index(op.f('ix_credential_created_at'), 'credential', ['created_at'])

    # Create response_pool table
    op.create_table(
        'response_pool',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('task_id', sa.UUID(), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_ok=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_response_pool_task_id'), 'response_pool', ['task_id'])
    op.create_index(op.f('ix_response_pool_created_at'), 'response_pool', ['created_at'])


def downgrade() -> None:
    op.drop_index(op.f('ix_response_pool_created_at'), table_name='response_pool')
    op.drop_index(op.f('ix_response_pool_task_id'), table_name='response_pool')
    op.drop_table('response_pool')
    
    op.drop_index(op.f('ix_credential_created_at'), table_name='credential')
    op.drop_index(op.f('ix_credential_name'), table_name='credential')
    op.drop_table('credential')
    
    op.drop_index(op.f('ix_task_created_at'), table_name='task')
    op.drop_index(op.f('ix_task_agent_id'), table_name='task')
    op.drop_index(op.f('ix_task_status'), table_name='task')
    op.drop_index(op.f('ix_task_application_id'), table_name='task')
    op.drop_table('task')
    
    op.drop_index(op.f('ix_application_created_at'), table_name='application')
    op.drop_index(op.f('ix_application_status'), table_name='application')
    op.drop_index(op.f('ix_application_program_id'), table_name='application')
    op.drop_table('application')
    
    op.drop_index(op.f('ix_program_created_at'), table_name='program')
    op.drop_index(op.f('ix_program_name'), table_name='program')
    op.drop_table('program')
