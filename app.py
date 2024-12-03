import os
# Application configuration
APP_NAME = "Market Harvest"

import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from extensions import init_extensions, db

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['APP_NAME'] = APP_NAME
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    init_extensions(app)
    
    with app.app_context():
        # Import models and blueprints
        from models import User
        from auth import auth_bp
        from profile import profile_bp
        from admin import admin_bp
        
        # Register blueprints
        app.register_blueprint(auth_bp)
        app.register_blueprint(profile_bp)
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
        
        # Create database tables
        db.create_all()
        
        # Configure Mailgun after database setup
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
        
        return app

from flask import redirect, url_for, render_template

app = create_app()
@app.route('/')
def index():
    return render_template('landing.html')


if __name__ == "__main__":
    # Run the application on port 5000 and bind to all network interfaces
    app.run(host="0.0.0.0", port=5000)
