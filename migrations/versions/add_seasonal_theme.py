"""Add seasonal theme column

Revision ID: add_seasonal_theme
Create Date: 2024-12-03
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('user', sa.Column('seasonal_theme', sa.String(20), nullable=True))
    op.execute("UPDATE user SET seasonal_theme = theme WHERE seasonal_theme IS NULL")
    op.execute("UPDATE user SET seasonal_theme = 'autumn' WHERE seasonal_theme NOT IN ('autumn', 'winter', 'spring', 'summer')")

def downgrade():
    op.drop_column('user', 'seasonal_theme')
