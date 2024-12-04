from decimal import Decimal
from typing import Tuple
from datetime import datetime
from models import User, UserBalance, TransactionHistory, CurrencyType, TransactionType
from extensions import db

# Conversion rates (base currency is Dabbers)
CONVERSION_RATES = {
    'dabber_to_groot': Decimal('10'),     # 10 Dabbers = 1 Groot
    'groot_to_petalin': Decimal('5'),     # 5 Groots = 1 Petalin
    'petalin_to_floren': Decimal('2'),    # 2 Petalins = 1 Floren
}

def get_conversion_rate(from_currency: str, to_currency: str) -> Decimal:
    """Calculate conversion rate between two currencies."""
    conversion_map = {
        ('dabber', 'groot'): CONVERSION_RATES['dabber_to_groot'],
        ('groot', 'petalin'): CONVERSION_RATES['groot_to_petalin'],
        ('petalin', 'floren'): CONVERSION_RATES['petalin_to_floren'],
        # Reverse conversions
        ('groot', 'dabber'): Decimal('1') / CONVERSION_RATES['dabber_to_groot'],
        ('petalin', 'groot'): Decimal('1') / CONVERSION_RATES['groot_to_petalin'],
        ('floren', 'petalin'): Decimal('1') / CONVERSION_RATES['petalin_to_floren']
    }
    
    return conversion_map.get((from_currency, to_currency), Decimal('0'))

def validate_conversion(user: User, from_currency: str, to_currency: str, amount: int) -> Tuple[bool, str]:
    """Validate if a currency conversion is possible."""
    if not user.balance:
        return False, "User has no balance record"
        
    if amount <= 0:
        return False, "Amount must be positive"
        
    current_balance = getattr(user.balance, f"{from_currency}s", 0)
    if current_balance < amount:
        return False, f"Insufficient {from_currency} balance"
        
    return True, "Conversion possible"

def convert_currency(user: User, from_currency: str, to_currency: str, amount: int) -> Tuple[bool, str]:
    """Convert currency from one type to another."""
    # Validate the conversion
    is_valid, message = validate_conversion(user, from_currency, to_currency, amount)
    if not is_valid:
        return False, message
        
    try:
        # Calculate conversion
        rate = get_conversion_rate(from_currency, to_currency)
        if rate == 0:
            return False, "Invalid conversion path"
            
        converted_amount = int(Decimal(amount) / rate)
        
        # Update balances
        from_balance = getattr(user.balance, f"{from_currency}s")
        to_balance = getattr(user.balance, f"{to_currency}s")
        
        setattr(user.balance, f"{from_currency}s", from_balance - amount)
        setattr(user.balance, f"{to_currency}s", to_balance + converted_amount)
        user.balance.last_updated = datetime.utcnow()
        
        # Record transaction
        transaction = TransactionHistory(
            user_id=user.id,
            currency_type=f"{from_currency}_to_{to_currency}",
            amount=amount,
            transaction_type=TransactionType.CONVERSION,
            description=f"Converted {amount} {from_currency}s to {converted_amount} {to_currency}s"
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return True, f"Successfully converted {amount} {from_currency}s to {converted_amount} {to_currency}s"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error during conversion: {str(e)}"

def get_user_balance(user: User) -> dict:
    """Get formatted user balance."""
    if not user.balance:
        return {
            'dabbers': 0,
            'groots': 0,
            'petalins': 0,
            'florens': 0
        }
    
    return {
        'dabbers': user.balance.dabbers,
        'groots': user.balance.groots,
        'petalins': user.balance.petalins,
        'florens': user.balance.florens
    }
