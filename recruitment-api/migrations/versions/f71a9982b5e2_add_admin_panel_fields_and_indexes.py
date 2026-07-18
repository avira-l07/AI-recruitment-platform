"""add_admin_panel_fields_and_indexes

Revision ID: f71a9982b5e2
Revises: 248a11b76dbc
Create Date: 2026-07-19 02:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = 'f71a9982b5e2'
down_revision: Union[str, None] = '248a11b76dbc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Batch alter table users to add new columns with server defaults
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False))
        batch_op.add_column(sa.Column('must_change_password', sa.Boolean(), server_default=sa.text('0'), nullable=False))
        batch_op.add_column(sa.Column('created_by_admin_id', sa.Integer(), sa.ForeignKey('users.id', name='fk_users_created_by_admin_id'), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
        batch_op.add_column(sa.Column('last_login_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('token_version', sa.Integer(), server_default=sa.text('1'), nullable=False))

    # Helper function to safely create index if not exists
    bind = op.get_bind()
    inspector = inspect(bind)

    def safe_create_index(index_name: str, table_name: str, columns: list):
        indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
        if index_name not in indexes:
            op.create_index(index_name, table_name, columns, unique=False)

    safe_create_index('ix_users_role', 'users', ['role'])
    safe_create_index('ix_users_is_active', 'users', ['is_active'])
    safe_create_index('ix_users_created_by_admin_id', 'users', ['created_by_admin_id'])
    safe_create_index('ix_jobs_created_by', 'jobs', ['created_by'])
    safe_create_index('ix_applications_job_id', 'applications', ['job_id'])
    safe_create_index('ix_applications_candidate_id', 'applications', ['candidate_id'])
    safe_create_index('ix_notifications_user_id', 'notifications', ['user_id'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    def safe_drop_index(index_name: str, table_name: str):
        indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
        if index_name in indexes:
            op.drop_index(index_name, table_name=table_name)

    safe_drop_index('ix_notifications_user_id', 'notifications')
    safe_drop_index('ix_applications_candidate_id', 'applications')
    safe_drop_index('ix_applications_job_id', 'applications')
    safe_drop_index('ix_jobs_created_by', 'jobs')
    safe_drop_index('ix_users_created_by_admin_id', 'users')
    safe_drop_index('ix_users_is_active', 'users')
    safe_drop_index('ix_users_role', 'users')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('token_version')
        batch_op.drop_column('last_login_at')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_by_admin_id')
        batch_op.drop_column('must_change_password')
        batch_op.drop_column('is_active')
