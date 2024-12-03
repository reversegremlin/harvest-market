"""Add user profile fields

Revision ID: add_user_profile_fields
Create Date: 2024-12-03
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add new columns
    op.add_column('user', sa.Column('first_name', sa.String(64), nullable=True))
    op.add_column('user', sa.Column('last_name', sa.String(64), nullable=True))
    op.add_column('user', sa.Column('timezone', sa.String(50), nullable=True))
    
    # Set default values for existing records
    op.execute("UPDATE \"user\" SET first_name = '' WHERE first_name IS NULL")
    op.execute("UPDATE \"user\" SET last_name = '' WHERE last_name IS NULL")
    op.execute("UPDATE \"user\" SET timezone = 'UTC' WHERE timezone IS NULL")
    
    # Make columns non-nullable
    op.alter_column('user', 'first_name',
                    existing_type=sa.String(64),
                    nullable=False)
    op.alter_column('user', 'last_name',
                    existing_type=sa.String(64),
                    nullable=False)
    op.alter_column('user', 'timezone',
                    existing_type=sa.String(50),
                    nullable=False)

def downgrade():
    op.drop_column('user', 'timezone')
    op.drop_column('user', 'last_name')
    op.drop_column('user', 'first_name')
