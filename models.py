from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db
from enum import Enum

class CurrencyType(str, Enum):
    DABBER = 'dabber'
    GROOT = 'groot'
    PETALIN = 'petalin'
    FLOREN = 'floren'

class TransactionType(str, Enum):
    CREDIT = 'credit'
    DEBIT = 'debit'
    CONVERSION = 'conversion'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(64), nullable=False, default='')
    last_name = db.Column(db.String(64), nullable=False, default='')
    timezone = db.Column(db.String(50), nullable=False, default='UTC')
    password_hash = db.Column(db.String(256))
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True)
    reset_token = db.Column(db.String(100), unique=True)
    theme = db.Column(db.String(20), default='light')  # Default theme (light/dark)
    seasonal_theme = db.Column(db.String(20), default='autumn')  # Seasonal theme
    avatar_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    terms_accepted = db.Column(db.DateTime, nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    age_verified = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Add relationship to UserBalance
    balance = db.relationship('UserBalance', backref='user', uselist=False)
    transactions = db.relationship('TransactionHistory', backref='user', lazy='dynamic')

class UserBalance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    dabbers = db.Column(db.Integer, nullable=False, default=500)
    groots = db.Column(db.Integer, nullable=False, default=0)
    petalins = db.Column(db.Integer, nullable=False, default=0)
    florens = db.Column(db.Integer, nullable=False, default=0)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class TransactionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    currency_type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=True)

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(128), nullable=False, default='Market Harvest')
    site_icon = db.Column(db.Text, nullable=True)  # Stores SVG content
    default_theme = db.Column(db.String(20), nullable=False, default='autumn')
    welcome_message = db.Column(db.Text, nullable=True)
    footer_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_settings(cls):
        """Get the current site settings or create default ones if they don't exist."""
        # Get all settings ordered by id descending
        all_settings = cls.query.order_by(cls.id.desc()).all()
        
        if len(all_settings) > 1:
            # Keep the latest record (highest ID)
            latest_settings = all_settings[0]
            
            # Delete all other records
            for old_settings in all_settings[1:]:
                db.session.delete(old_settings)
            
            db.session.commit()
            return latest_settings
        
        # If no settings exist, create default ones
        if not all_settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
            return settings
            
        # Return the only existing record
        return all_settings[0]
