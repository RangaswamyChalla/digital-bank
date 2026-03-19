"""Initial schema - create all tables

Revision ID: 001
Revises:
Create Date: 2026-03-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='customer'),
        sa.Column('kyc_level', sa.Integer, server_default='0'),
        sa.Column('kyc_status', sa.String(20), server_default='pending'),
        sa.Column('kyc_document_type', sa.String(50), nullable=True),
        sa.Column('kyc_document_number', sa.String(100), nullable=True),
        sa.Column('kyc_document_file', sa.String(255), nullable=True),
        sa.Column('kyc_address', sa.Text, nullable=True),
        sa.Column('kyc_submitted_at', sa.DateTime, nullable=True),
        sa.Column('kyc_reviewed_at', sa.DateTime, nullable=True),
        sa.Column('kyc_reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('kyc_rejection_reason', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('failed_login_attempts', sa.Integer, server_default='0'),
        sa.Column('locked_until', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('admin_role_id', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Create accounts table
    op.create_table(
        'accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_number', sa.String(10), nullable=False, unique=True),
        sa.Column('account_type', sa.String(20), nullable=False),
        sa.Column('balance', sa.Numeric(15, 2), server_default='0'),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('from_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('to_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('from_account_number', sa.String(10), nullable=False),
        sa.Column('to_account_number', sa.String(10), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('transfer_type', sa.String(20), nullable=False),
        sa.Column('reference', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('merchant', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('failed_at', sa.DateTime, nullable=True),
        sa.Column('failure_reason', sa.Text, nullable=True),
    )

    # Create indexes for transactions
    op.create_index('ix_transactions_from_account_id', 'transactions', ['from_account_id'])
    op.create_index('ix_transactions_to_account_id', 'transactions', ['to_account_id'])
    op.create_index('ix_transactions_from_account_number', 'transactions', ['from_account_number'])
    op.create_index('ix_transactions_to_account_number', 'transactions', ['to_account_number'])
    op.create_index('ix_transactions_status', 'transactions', ['status'])
    op.create_index('ix_transactions_created_at', 'transactions', ['created_at'])
    op.create_index('ix_transactions_from_account_created', 'transactions', ['from_account_id', 'created_at'])
    op.create_index('ix_transactions_to_account_created', 'transactions', ['to_account_id', 'created_at'])
    op.create_index('ix_transactions_status_created', 'transactions', ['status', 'created_at'])

    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token', sa.String(500), nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create fraud_alerts table
    op.create_table(
        'fraud_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transactions.id'), nullable=True),
        sa.Column('risk_score', sa.Float, server_default='0.0'),
        sa.Column('risk_level', sa.String(20), server_default='low'),
        sa.Column('reasons', sa.String(1000), nullable=True),
        sa.Column('recommended_action', sa.String(50), server_default='ALLOW'),
        sa.Column('status', sa.String(20), server_default='open'),
        sa.Column('admin_action', sa.String(100), nullable=True),
        sa.Column('admin_notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
    )

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('is_read', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create admin_roles table
    op.create_table(
        'admin_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create admin_role_permissions association table
    op.create_table(
        'admin_role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('admin_roles.id'), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permissions.id'), primary_key=True),
    )

    # Create activity_logs table
    op.create_table(
        'activity_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(200), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', sa.String(1000), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(300), nullable=True),
        sa.Column('status', sa.String(20), server_default='success'),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Add foreign key for admin_role_id in users table
    op.create_foreign_key('fk_users_admin_role', 'users', 'admin_roles', ['admin_role_id'], ['id'])


def downgrade() -> None:
    op.drop_table('activity_logs')
    op.drop_table('admin_role_permissions')
    op.drop_table('permissions')
    op.drop_table('admin_roles')
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('fraud_alerts')
    op.drop_table('refresh_tokens')
    op.drop_index('ix_transactions_status_created', table_name='transactions')
    op.drop_index('ix_transactions_to_account_created', table_name='transactions')
    op.drop_index('ix_transactions_from_account_created', table_name='transactions')
    op.drop_index('ix_transactions_created_at', table_name='transactions')
    op.drop_index('ix_transactions_status', table_name='transactions')
    op.drop_index('ix_transactions_to_account_number', table_name='transactions')
    op.drop_index('ix_transactions_from_account_number', table_name='transactions')
    op.drop_index('ix_transactions_to_account_id', table_name='transactions')
    op.drop_index('ix_transactions_from_account_id', table_name='transactions')
    op.drop_table('transactions')
    op.drop_table('accounts')
    op.drop_table('users')
