"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-08-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    
    # Create classifications table
    op.create_table(
        'classifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.String(), nullable=False),
        sa.Column('contact', sa.String(), nullable=True),
        sa.Column('dealer_name', sa.String(), nullable=True),
        sa.Column('dealer_id', sa.String(), nullable=True),
        sa.Column('rep', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('sub_category', sa.String(), nullable=True),
        sa.Column('syndicator', sa.String(), nullable=True),
        sa.Column('inventory_type', sa.String(), nullable=True),
        sa.Column('is_pushed', sa.Boolean(), default=False),
        sa.Column('pushed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('raw_classification', sa.JSON(), nullable=True),
        sa.Column('ticket_subject', sa.String(), nullable=True),
        sa.Column('ticket_content', sa.Text(), nullable=True),
        sa.Column('ticket_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_classifications_ticket_id'), 'classifications', ['ticket_id'], unique=False)
    op.create_index(op.f('ix_classifications_dealer_name'), 'classifications', ['dealer_name'], unique=False)
    op.create_index(op.f('ix_classifications_dealer_id'), 'classifications', ['dealer_id'], unique=False)
    op.create_index(op.f('ix_classifications_rep'), 'classifications', ['rep'], unique=False)
    op.create_index(op.f('ix_classifications_category'), 'classifications', ['category'], unique=False)
    op.create_index(op.f('ix_classifications_sub_category'), 'classifications', ['sub_category'], unique=False)
    op.create_index(op.f('ix_classifications_syndicator'), 'classifications', ['syndicator'], unique=False)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('classification_id', sa.Integer(), sa.ForeignKey('classifications.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    
    # Create dealers table
    op.create_table(
        'dealers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dealer_id', sa.String(), nullable=False),
        sa.Column('dealer_name', sa.String(), nullable=False),
        sa.Column('rep_name', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('province', sa.String(), nullable=True),
        sa.Column('postal_code', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dealer_id'),
    )
    op.create_index(op.f('ix_dealers_dealer_id'), 'dealers', ['dealer_id'], unique=True)
    op.create_index(op.f('ix_dealers_dealer_name'), 'dealers', ['dealer_name'], unique=False)
    op.create_index(op.f('ix_dealers_rep_name'), 'dealers', ['rep_name'], unique=False)
    
    # Create syndicators table
    op.create_table(
        'syndicators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_syndicators_name'), 'syndicators', ['name'], unique=True)
    
    # Create zoho_tokens table
    op.create_table(
        'zoho_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('access_token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('zoho_tokens')
    op.drop_table('syndicators')
    op.drop_table('dealers')
    op.drop_table('audit_logs')
    op.drop_table('classifications')
    op.drop_table('users')