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
from threading import Lock

# Create a thread-safe lock for site settings
_settings_lock = Lock()

@app.context_processor
def inject_site_settings():
    def get_settings():
        from models import SiteSettings
        
        # Default settings as a class
        class BaseSettings:
            site_title = 'Market Harvest'
            welcome_message = 'Welcome to our vibrant community!'
            footer_text = '© 2024 Market Harvest. All rights reserved.'
            default_theme = 'autumn'
            site_icon = None
            created_at = None
            updated_at = None

        # Ensure database connection is available
        try:
            db.engine.connect().close()
        except Exception as e:
            app.logger.error(f'Database connection error: {str(e)}')
            return BaseSettings()
        
        with _settings_lock:
            try:
                # Query settings in a transaction
                with db.session.begin():
                    settings = SiteSettings.query.with_for_update().first()
                    if settings:
                        # Verify all required attributes exist
                        for attr in dir(BaseSettings):
                            if not attr.startswith('_'):
                                if not hasattr(settings, attr):
                                    setattr(settings, attr, getattr(BaseSettings, attr))
                        db.session.commit()
                        return settings
                    
                    # Create new settings if none exist
                    app.logger.info('No settings found in database, creating defaults')
                    new_settings = SiteSettings()
                    for attr in dir(BaseSettings):
                        if not attr.startswith('_'):
                            setattr(new_settings, attr, getattr(BaseSettings, attr))
                    db.session.add(new_settings)
                    db.session.commit()
                    return new_settings
                    
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'Error accessing site settings: {str(e)}')
                return BaseSettings()

    return dict(site_settings=get_settings)

@app.template_filter('b64encode')
def b64encode_filter(s):
    if s is None:
        return ''
    return b64encode(s.encode()).decode()

@app.route('/')
def index():
    from flask_login import current_user
    
    try:
        # Get authenticated user's theme if available
        theme = current_user.theme if current_user.is_authenticated else 'autumn'
        
        app.logger.info(f'Rendering landing page with theme: {theme}')
        return render_template('landing.html', theme=theme)
        
    except Exception as e:
        app.logger.error(f'Error rendering landing page: {str(e)}')
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



def find_available_port(start_port, max_port=65535):
    """Find an available port starting from start_port."""
    import socket
    current_port = start_port
    while current_port <= max_port:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', current_port))
                return current_port
        except OSError:
            current_port += 1
    raise OSError(f"No available ports found between {start_port} and {max_port}")

if __name__ == "__main__":
    # Get port from environment variable or use default 5000
    port = int(os.environ.get('PORT', 5000))
    
    try:
        # Initialize application and database
        with app.app_context():
            app.logger.info("Testing database connection...")
            db.engine.connect().close()
            app.logger.info("Database connection successful")
            
            app.logger.info("Creating database tables...")
            db.create_all()
            app.logger.info("Database tables created successfully")
            
            # Pre-check site settings
            from models import SiteSettings
            if not SiteSettings.query.first():
                app.logger.info("Initializing default site settings...")
                default_settings = SiteSettings(
                    site_title='Market Harvest',
                    welcome_message='Welcome to our vibrant community!',
                    footer_text='© 2024 Market Harvest. All rights reserved.',
                    default_theme='autumn'
                )
                db.session.add(default_settings)
                db.session.commit()
                app.logger.info("Default site settings created")
        
        app.logger.info(f"Starting server on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        app.logger.error(f"Failed to start server: {str(e)}")
        if hasattr(e, '__cause__') and e.__cause__:
            app.logger.error(f"Caused by: {str(e.__cause__)}")
        raise
