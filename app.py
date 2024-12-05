import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, redirect, url_for, render_template
from flask import request, jsonify
from base64 import b64encode

# Application configuration
APP_NAME = "Market Harvest"

# Create Flask application
app = Flask(__name__)

# Basic configuration
app.config['APP_NAME'] = APP_NAME
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev')

# Initialize database first
from extensions import db, migrate
# Initialize all extensions
from extensions import init_extensions
init_extensions(app)

# Import blueprints after extensions are initialized
from models import User
from auth import auth_bp
from flask_wtf.csrf import CSRFProtect
from profile import profile_bp
from admin import admin_bp

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(profile_bp, url_prefix='/profile')
app.register_blueprint(admin_bp)

# Set up logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/auth_system.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Auth system startup')

# Configure Mailgun
app.config['MAILGUN_API_KEY'] = os.environ.get('MAILGUN_API_KEY')
app.config['MAILGUN_DOMAIN'] = os.environ.get('MAILGUN_DOMAIN')

# Verify Mailgun configuration and set up email sender
if app.config['MAILGUN_API_KEY'] and app.config['MAILGUN_DOMAIN']:
    app.config['MAIL_DEFAULT_SENDER'] = f"Market Harvest <noreply@{app.config['MAILGUN_DOMAIN']}>"
    app.logger.info('Mailgun configuration loaded successfully')
else:
    missing_configs = []
    if not app.config['MAILGUN_API_KEY']:
        missing_configs.append('MAILGUN_API_KEY')
    if not app.config['MAILGUN_DOMAIN']:
        missing_configs.append('MAILGUN_DOMAIN')
    app.logger.warning(f'Mailgun configuration incomplete. Missing: {", ".join(missing_configs)}. Email features will be disabled.')
# Add template context processors and filters
@app.context_processor
def inject_site_settings():
    from models import SiteSettings
    def get_settings():
        try:
            # Attempt to get existing settings
            settings = SiteSettings.query.first()
            
            if not settings:
                try:
                    # Create default settings if none exist
                    settings = SiteSettings(
                        site_title='Market Harvest',
                        welcome_message='Welcome to our vibrant community!',
                        footer_text='© 2024 Market Harvest. All rights reserved.',
                        default_theme='autumn'
                    )
                    db.session.add(settings)
                    db.session.commit()
                    app.logger.info('Created default site settings')
                except Exception as e:
                    app.logger.error(f'Failed to create default settings: {str(e)}')
                    db.session.rollback()
            
            if settings:
                app.logger.debug(f'Using database settings - title: {settings.site_title}')
                return settings
        except Exception as e:
            app.logger.error(f'Error accessing site settings: {str(e)}')
        
        # Return default settings object if anything fails
        return type('DefaultSettings', (), {
            'site_title': 'Market Harvest',
            'welcome_message': 'Welcome to our vibrant community!',
            'footer_text': '© 2024 Market Harvest. All rights reserved.',
            'default_theme': 'autumn',
            'site_icon': None
        })
    return dict(site_settings=get_settings)

@app.template_filter('b64encode')
def b64encode_filter(s):
    if s is None:
        return ''
    return b64encode(s.encode()).decode()

@app.route('/')
def index():
    try:
        # Set default theme and settings
        theme = 'autumn'
        settings = None
        
        try:
            # Attempt to get site settings
            settings = inject_site_settings()['site_settings']()
            if settings and settings.default_theme:
                theme = settings.default_theme
        except Exception as e:
            app.logger.error(f'Error accessing site settings: {str(e)}')
            # Continue with default theme if settings access fails
        
        return render_template('landing.html', theme=theme)
    except Exception as e:
        app.logger.error(f'Error loading landing page: {str(e)}')
        # Return basic landing page with default theme
        return render_template('landing.html', theme='autumn')
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')
@app.route('/terms')
def terms():
    return render_template('terms.html')
@app.context_processor
def utility_processor():
    from datetime import datetime
    return {'now': datetime.utcnow()}

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/log-consent', methods=['POST'])
def log_consent():
    try:
        data = request.get_json()
        consent = data.get('consent', False)
        timestamp = data.get('timestamp')
        
        app.logger.info(f'Cookie consent logged - Status: {consent}, Timestamp: {timestamp}')
        return {'status': 'success'}, 200
        
    except Exception as e:
        app.logger.error(f'Error logging cookie consent: {str(e)}')
        return {'status': 'error', 'message': 'Failed to log consent'}, 500



if __name__ == "__main__":
    # Run the application on port 5000 and bind to all network interfaces
    app.run(host="0.0.0.0", port=5000)
