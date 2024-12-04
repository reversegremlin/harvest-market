"""add currency tables

Revision ID: add_currency_tables
Revises: consolidated_migration
Create Date: 2024-12-04 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic
revision = 'add_currency_tables'
down_revision = 'consolidated_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Create UserBalance table
    op.create_table('user_balance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('dabbers', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('groots', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('petalins', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('florens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create TransactionHistory table
    op.create_table('transaction_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('currency_type', sa.String(10), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(10), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create initial balances for existing users
    op.execute("""
        INSERT INTO user_balance (user_id, dabbers, groots, petalins, florens, last_updated)
        SELECT id, 500, 0, 0, 0, CURRENT_TIMESTAMP
        FROM "user"
        WHERE id NOT IN (SELECT user_id FROM user_balance)
    """)

def downgrade():
    op.drop_table('transaction_history')
    op.drop_table('user_balance')
