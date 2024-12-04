"""update theme field to light dark

Revision ID: update_theme_field
Revises: update_currency_conversion_rates
Create Date: 2024-12-04 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'update_theme_field'
down_revision = 'update_currency_conversion_rates'
branch_labels = None
depends_on = None

def upgrade():
    # First, update existing theme values to 'light' (default theme)
    op.execute("""
        UPDATE "user"
        SET seasonal_theme = 'light'
        WHERE seasonal_theme IN ('spring', 'summer', 'autumn', 'winter')
    """)
    
    # Rename column and update type constraints
    op.alter_column('user', 'seasonal_theme',
                    new_column_name='theme',
                    existing_type=sa.String(length=10),
                    existing_nullable=False,
                    server_default='light')

def downgrade():
    # Rename back to seasonal_theme
    op.alter_column('user', 'theme',
                    new_column_name='seasonal_theme',
                    existing_type=sa.String(length=10),
                    existing_nullable=False,
                    server_default='autumn')
