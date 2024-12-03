import os
# Application configuration
APP_NAME = "Market Harvest"

import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['APP_NAME'] = APP_NAME
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Mail configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
    
    # Verify mail configuration
    if not all([app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']]):
        app.logger.warning('Email configuration incomplete. Some features may not work properly.')
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    # Set up login view
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    with app.app_context():
        # Import models and blueprints
        from models import User
        from auth import auth_bp
        from profile import profile_bp
        
        # Register blueprints
        app.register_blueprint(auth_bp)
        app.register_blueprint(profile_bp)
        
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
        
        return app

from flask import redirect, url_for, render_template

app = create_app()
@app.route('/')
def index():
    return render_template('landing.html')


@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
