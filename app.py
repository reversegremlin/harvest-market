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

# Configure logging format
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

# File handler for all levels
file_handler = RotatingFileHandler('logs/auth_system.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# Stream handler for console output
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.DEBUG)

# Set up app logger
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)
app.logger.setLevel(logging.DEBUG)

# Log startup information
app.logger.info('Auth system startup')
app.logger.debug('Debug logging enabled')

# Log configuration status
app.logger.debug(f'SQLALCHEMY_DATABASE_URI configured: {bool(app.config.get("SQLALCHEMY_DATABASE_URI"))}')
app.logger.debug(f'SECRET_KEY configured: {bool(app.config.get("SECRET_KEY"))}')
app.logger.debug(f'WTF_CSRF_ENABLED: {app.config.get("WTF_CSRF_ENABLED")}')

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
    app.logger.debug('Starting site settings injection')
    
    # Default settings
    DEFAULT_SETTINGS = {
        'site_title': 'Market Harvest',
        'welcome_message': 'Welcome to our vibrant community!',
        'footer_text': '© 2024 Market Harvest. All rights reserved.',
        'default_theme': 'autumn',
        'site_icon': None
    }

    try:
        from models import SiteSettings
        app.logger.debug('Fetching site settings from database')
        settings = SiteSettings.get_settings()
        
        if settings:
            app.logger.debug(f'Found settings with ID: {settings.id}')
            # Create a dictionary with all required attributes
            settings_dict = {
                'site_title': settings.site_title or DEFAULT_SETTINGS['site_title'],
                'welcome_message': settings.welcome_message or DEFAULT_SETTINGS['welcome_message'],
                'footer_text': settings.footer_text or DEFAULT_SETTINGS['footer_text'],
                'default_theme': settings.default_theme or DEFAULT_SETTINGS['default_theme'],
                'site_icon': settings.site_icon
            }
            app.logger.debug(f'Created settings dictionary with theme: {settings_dict["default_theme"]}')
        else:
            app.logger.warning('No settings found in database, using defaults')
            settings_dict = DEFAULT_SETTINGS.copy()
        
        # Convert to an object for attribute access
        settings_obj = type('Settings', (), settings_dict)()
        app.logger.debug('Successfully created settings object')
        return {'site_settings': settings_obj}
        
    except Exception as e:
        app.logger.error(f'Error in site settings context processor: {str(e)}')
        app.logger.exception('Full traceback:')
        # Return default settings as an object
        return {'site_settings': type('DefaultSettings', (), DEFAULT_SETTINGS)()}

@app.template_filter('b64encode')
def b64encode_filter(s):
    if s is None:
        return ''
    return b64encode(s.encode()).decode()

@app.route('/')
def index():
    from flask_login import current_user
    
    app.logger.info('Processing index route request')
    # Set default theme
    theme = 'autumn'
    
    try:
        if current_user.is_authenticated:
            app.logger.debug(f'User authenticated: {current_user.username}')
            user_theme = getattr(current_user, 'theme', None)
            app.logger.debug(f'User theme preference: {user_theme}')
            theme = user_theme if user_theme else theme
            app.logger.debug(f'Selected theme for authenticated user: {theme}')
        else:
            app.logger.debug('Anonymous user, fetching default theme from settings')
            settings = inject_site_settings()['site_settings']
            app.logger.debug(f'Site settings loaded with default theme: {getattr(settings, "default_theme", None)}')
            theme = settings.default_theme if hasattr(settings, 'default_theme') else theme
            app.logger.debug(f'Final theme for anonymous user: {theme}')
            
        app.logger.info(f'Rendering landing page with theme: {theme}')
        template_response = render_template('landing.html', theme=theme)
        app.logger.debug('Template rendered successfully')
        return template_response
        
    except Exception as e:
        app.logger.error(f'Error in index route: {str(e)}')
        app.logger.exception('Full traceback:')
        # Continue with default theme
        app.logger.info(f'Falling back to default theme: {theme}')
    
    return render_template('landing.html', theme=theme)
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
