from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db

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
    theme = db.Column(db.String(20), default='autumn')  # Changed default to autumn
    seasonal_theme = db.Column(db.String(20), default='autumn')  # Added seasonal theme
    avatar_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    terms_accepted = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
