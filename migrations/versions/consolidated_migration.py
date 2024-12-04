"""consolidated migration

Revision ID: consolidated_migration
Revises: 
Create Date: 2024-12-04 05:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, date

# revision identifiers, used by Alembic.
revision = 'consolidated_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to user table if they don't exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = {col['name'] for col in inspector.get_columns('user')}

    # Add missing columns to user table
    columns_to_add = {
        'first_name': sa.String(64),
        'last_name': sa.String(64),
        'timezone': sa.String(50),
        'seasonal_theme': sa.String(20),
        'is_admin': sa.Boolean(),
        'terms_accepted': sa.DateTime(),
        'birth_date': sa.Date(),
        'age_verified': sa.Boolean()
    }

    for col_name, col_type in columns_to_add.items():
        if col_name not in existing_columns:
            op.add_column('user', sa.Column(col_name, col_type, nullable=True))

    # Create site_settings table if it doesn't exist
    if 'site_settings' not in inspector.get_table_names():
        op.create_table('site_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('site_title', sa.String(length=128), nullable=False),
            sa.Column('site_icon', sa.Text(), nullable=True),
            sa.Column('default_theme', sa.String(length=20), nullable=False),
            sa.Column('welcome_message', sa.Text(), nullable=True),
            sa.Column('footer_text', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

        # Insert default site settings
        op.execute("""
        INSERT INTO site_settings (site_title, default_theme, created_at, updated_at)
        VALUES ('Market Harvest', 'autumn', NOW(), NOW())
        """)

    # Set default values for existing rows
    op.execute("UPDATE \"user\" SET theme = 'autumn' WHERE theme IS NULL")
    op.execute("UPDATE \"user\" SET seasonal_theme = 'autumn' WHERE seasonal_theme IS NULL")
    op.execute("UPDATE \"user\" SET is_admin = FALSE WHERE is_admin IS NULL")
    op.execute("UPDATE \"user\" SET email_verified = FALSE WHERE email_verified IS NULL")
    op.execute("UPDATE \"user\" SET age_verified = FALSE WHERE age_verified IS NULL")
    op.execute("UPDATE \"user\" SET created_at = NOW() WHERE created_at IS NULL")
    op.execute("UPDATE \"user\" SET first_name = '' WHERE first_name IS NULL")
    op.execute("UPDATE \"user\" SET last_name = '' WHERE last_name IS NULL")
    op.execute("UPDATE \"user\" SET timezone = 'UTC' WHERE timezone IS NULL")

def downgrade():
    # We don't want to drop tables or remove columns in downgrade
    pass
