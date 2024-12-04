"""add birth date fields with default value

Revision ID: add_birth_date_fields
Revises: 0eb6e26b4a73
Create Date: 2024-12-04 05:30:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import date

# revision identifiers, used by Alembic.
revision = 'add_birth_date_fields'
down_revision = '0eb6e26b4a73'
branch_labels = None
depends_on = None

def upgrade():
    # Add columns as nullable first
    op.add_column('user', sa.Column('birth_date', sa.Date(), nullable=True))
    op.add_column('user', sa.Column('age_verified', sa.Boolean(), nullable=True))
    
    # Set default values for existing records (18 years ago from today)
    default_birth_date = date(2006, 12, 4)  # 18 years ago
    op.execute(f"UPDATE \"user\" SET birth_date = '{default_birth_date}' WHERE birth_date IS NULL")
    op.execute("UPDATE \"user\" SET age_verified = TRUE WHERE age_verified IS NULL")
    
    # Make columns non-nullable
    op.alter_column('user', 'birth_date',
                    existing_type=sa.Date(),
                    nullable=False)
    op.alter_column('user', 'age_verified',
                    existing_type=sa.Boolean(),
                    nullable=False,
                    server_default=sa.text('false'))

def downgrade():
    op.drop_column('user', 'age_verified')
    op.drop_column('user', 'birth_date')
