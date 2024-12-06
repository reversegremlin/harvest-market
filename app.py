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
    from models import SiteSettings
    from sqlalchemy.exc import SQLAlchemyError
    
    # Default settings as a class for better attribute access
    class DefaultSettings:
        def __init__(self):
            self.site_title = 'Market Harvest'
            self.welcome_message = 'Welcome to our vibrant community!'
            self.footer_text = '© 2024 Market Harvest. All rights reserved.'
            self.default_theme = 'autumn'
            self.site_icon = None
    
    try:
        # Create a new session for this request
        settings = None
        with app.app_context():
            try:
                # Try to get existing settings
                settings = db.session.query(SiteSettings).first()
                
                if not settings:
                    # Log the attempt to create new settings
                    app.logger.info('No settings found, creating defaults')
                    
                    # Create new settings
                    default = DefaultSettings()
                    settings = SiteSettings(
                        site_title=default.site_title,
                        welcome_message=default.welcome_message,
                        footer_text=default.footer_text,
                        default_theme=default.default_theme
                    )
                    
                    # Add and commit in a transaction
                    db.session.add(settings)
                    db.session.commit()
                    app.logger.info('Default settings created successfully')
                
                # Make sure to load the attributes before closing the session
                settings.site_title
                settings.welcome_message
                settings.footer_text
                settings.default_theme
                settings.site_icon
                
            except SQLAlchemyError as e:
                db.session.rollback()
                app.logger.error(f'Database error in site settings: {str(e)}')
                settings = DefaultSettings()
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'Unexpected error in site settings: {str(e)}')
                settings = DefaultSettings()
            finally:
                db.session.close()
        
        return dict(site_settings=settings if settings else DefaultSettings())
        
    except Exception as e:
        app.logger.error(f'Critical error in site settings context processor: {str(e)}')
        return dict(site_settings=DefaultSettings())

@app.template_filter('b64encode')
def b64encode_filter(s):
    if s is None:
        return ''
    return b64encode(s.encode()).decode()

@app.route('/')
def index():
    from flask_login import current_user
    
    try:
        # Get authenticated user's theme if available, otherwise use default from site settings
        if current_user.is_authenticated:
            theme = current_user.theme
        else:
            # Get site settings and use default theme, fall back to autumn if needed
            settings = inject_site_settings()['site_settings']
            theme = getattr(settings, 'default_theme', 'autumn')
        
        app.logger.info(f'Rendering landing page with theme: {theme}')
        return render_template('landing.html', theme=theme)
        
    except Exception as e:
        app.logger.error(f'Error rendering landing page: {str(e)}')
        # Use autumn theme as ultimate fallback
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
