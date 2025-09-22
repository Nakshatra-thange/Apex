"""Create all tables from a truly clean slate

Revision ID: 3d0baf7fbdf2
Revises: 
Create Date: 2025-09-20 18:38:50.561526

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d0baf7fbdf2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### MANUALLY CORRECTED SCRIPT ###
    
    # Step 1: Manually create the ENUM types first.
    op.execute("CREATE TYPE userrole AS ENUM ('free_user', 'premium_user', 'admin')")
    op.execute("CREATE TYPE projectrole AS ENUM ('owner', 'editor', 'viewer')")
    
    # Step 2: Create tables in the correct dependency order.
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', postgresql.ENUM('free_user', 'premium_user', 'admin', name='userrole', create_type=False), server_default='free_user', nullable=False),
        sa.Column('subscription_tier', sa.String(), server_default='free', nullable=False),
        sa.Column('status', sa.String(), server_default='active', nullable=False),
        sa.Column('email_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.UUID(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    
    op.create_table('projects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)
    
    op.create_table('password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_reset_tokens_token_hash'), 'password_reset_tokens', ['token_hash'], unique=True)
    
    op.create_table('project_members',
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', postgresql.ENUM('owner', 'editor', 'viewer', name='projectrole', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('project_id', 'user_id')
    )
    
    op.create_table('refresh_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('device_info', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    
    op.create_table('code_snippets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('language', sa.String(), nullable=False),
        sa.Column('hash', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_code_snippets_hash'), 'code_snippets', ['hash'], unique=True)
    op.create_index(op.f('ix_code_snippets_language'), 'code_snippets', ['language'], unique=False)
    
    op.create_table('reviews',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code_snippet_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('progress_stage', sa.String(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['code_snippet_id'], ['code_snippets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reviews_status'), 'reviews', ['status'], unique=False)


def downgrade() -> None:
    # Drop in the reverse order of creation
    op.drop_index(op.f('ix_reviews_status'), table_name='reviews')
    op.drop_table('reviews')
    op.drop_index(op.f('ix_code_snippets_language'), table_name='code_snippets')
    op.drop_index(op.f('ix_code_snippets_hash'), table_name='code_snippets')
    op.drop_table('code_snippets')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_table('project_members')
    op.drop_index(op.f('ix_password_reset_tokens_token_hash'), table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_index(op.f('ix_projects_name'), table_name='projects')
    op.drop_table('projects')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop the ENUM types last
    op.execute("DROP TYPE projectrole")
    op.execute("DROP TYPE userrole")