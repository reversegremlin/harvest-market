"""update currency conversion rates

Revision ID: update_currency_conversion_rates
Revises: add_currency_tables
Create Date: 2024-12-04 16:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from decimal import Decimal

# revision identifiers, used by Alembic
revision = 'update_currency_conversion_rates'
down_revision = 'add_currency_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Get bind and create session
    bind = op.get_bind()
    session = Session(bind=bind)
    
    # Update all user balances to reflect new conversion rates
    # We'll convert all currency to Dabbers first, then redistribute according to new rates
    from sqlalchemy import text
    
    session.execute(text("""
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
            dabbers = utd.total_dabbers % 1000
        FROM user_total_dabbers utd
        WHERE ub.user_id = utd.user_id;
    """))
    
    session.commit()

def downgrade():
    # Since this is a data migration changing conversion rates,
    # we don't provide a downgrade path as it would be complex
    # to determine the exact previous state
    pass
