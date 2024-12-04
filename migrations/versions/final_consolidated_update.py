"""final consolidated update

Revision ID: final_consolidated_update
Revises: consolidated_migration
Create Date: 2024-12-04 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic
revision = 'final_consolidated_update'
down_revision = 'consolidated_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Get bind and create session
    bind = op.get_bind()
    session = Session(bind=bind)
    
    # Create user_balance table if it doesn't exist
    if not op.get_bind().dialect.has_table(op.get_bind(), 'user_balance'):
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

        # Create transaction_history table if it doesn't exist
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
        session.execute("""
            INSERT INTO user_balance (user_id, dabbers, groots, petalins, florens, last_updated)
            SELECT id, 500, 0, 0, 0, CURRENT_TIMESTAMP
            FROM "user"
            WHERE id NOT IN (SELECT user_id FROM user_balance)
        """)

    # Update currency conversion rates and convert existing balances
    session.execute("""
        WITH user_total_dabbers AS (
            SELECT 
                user_id,
                (dabbers + groots * 1000 + petalins * 100000 + florens * 1000000) as total_dabbers
            FROM user_balance
        )
        UPDATE user_balance ub
        SET 
            florens = FLOOR(utd.total_dabbers / 1000000),
            petalins = FLOOR((utd.total_dabbers % 1000000) / 100000),
            groots = FLOOR((utd.total_dabbers % 100000) / 1000),
            dabbers = utd.total_dabbers % 1000,
            last_updated = CURRENT_TIMESTAMP
        FROM user_total_dabbers utd
        WHERE ub.user_id = utd.user_id;
    """)
    
    session.commit()

def downgrade():
    # We don't want to revert these changes as it would be complex and potentially lose data
    pass
