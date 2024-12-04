"""update currency rates and convert balances

Revision ID: update_currency_rates
Revises: add_currency_tables
Create Date: 2024-12-04 23:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic
revision = 'update_currency_rates'
down_revision = 'add_currency_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Get bind and create session
    bind = op.get_bind()
    session = Session(bind=bind)
    
    # Update balances with new conversion rates:
    # 1 groot = 1000 dabbers
    # 1 petalin = 100 groots
    # 1 floren = 10 petalins
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
    
    # Record the conversion in transaction history
    session.execute("""
        INSERT INTO transaction_history (user_id, currency_type, amount, transaction_type, description)
        SELECT 
            user_id,
            'all',
            0,
            'conversion',
            'Currency conversion rates updated: 1 Groot = 1000 Dabbers, 1 Petalin = 100 Groots, 1 Floren = 10 Petalins'
        FROM user_balance;
    """)
    
    session.commit()

def downgrade():
    # We don't want to revert the conversion as it would be complex and potentially lose data
    pass
