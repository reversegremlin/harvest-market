from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app as app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
import secrets
from app import db, mail
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Input validation
        if not all([email, username, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.register'))
            
        # Username format validation
        if not username.isalnum() and '_' not in username:
            flash('Username can only contain letters, numbers, and underscores', 'error')
            return redirect(url_for('auth.register'))
            
        if len(username) < 3 or len(username) > 20:
            flash('Username must be between 3 and 20 characters', 'error')
            return redirect(url_for('auth.register'))

        # Check existing users
        if User.query.filter_by(email=email).first():
            app.logger.warning(f'Registration attempted with existing email: {email}')
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(username=username).first():
            app.logger.warning(f'Registration attempted with existing username: {username}')
            flash('Username already taken', 'error')
            return redirect(url_for('auth.register'))

        try:
            # Start database transaction
            user = User(email=email, username=username)
            user.set_password(password)
            user.verification_token = secrets.token_urlsafe(32)
            user.avatar_url = f"https://api.dicebear.com/6.x/avataaars/svg?seed={username}"
            
            db.session.add(user)
            
            # Verify email configuration
            if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
                raise ValueError('Email configuration is incomplete')
                
            # Prepare verification email
            msg = Message('Welcome to SecureAuth - Verify your email',
                         sender=app.config['MAIL_USERNAME'],
                         recipients=[email])
            msg.html = render_template('emails/verify.html', 
                                     token=user.verification_token)
            
            # Send email and commit transaction
            mail.send(msg)
            db.session.commit()
            
            app.logger.info(f'New user registered successfully: {username} ({email})')
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('auth.login'))
            
        except ValueError as e:
            db.session.rollback()
            app.logger.error(f'Configuration error during registration: {str(e)}')
            flash('System configuration error. Please contact support.', 'error')
            return redirect(url_for('auth.register'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error during registration for {email}: {str(e)}')
            if 'smtp' in str(e).lower():
                flash('Unable to send verification email. Please try again later.', 'error')
            else:
                flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('auth.register'))
            
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.email_verified:
                flash('Please verify your email address first.', 'warning')
                return redirect(url_for('auth.login'))
                
            login_user(user, remember=remember)
            app.logger.info(f'User logged in: {user.username}')
            return redirect(url_for('profile.dashboard'))
            
        flash('Invalid email or password', 'error')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user:
        user.email_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Your email has been verified. You can now login.', 'success')
        app.logger.info(f'Email verified for user: {user.username}')
    else:
        flash('Invalid verification token.', 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            db.session.commit()
            
            msg = Message('Reset your password',
                         sender=app.config['MAIL_USERNAME'],
                         recipients=[email])
            msg.html = render_template('emails/reset_password.html', token=token)
            mail.send(msg)
            
            flash('Password reset instructions sent to your email.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html')

@auth_bp.route('/test-email')
def test_email():
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        app.logger.error('Email configuration missing')
        return 'Email configuration missing. Please check MAIL_USERNAME and MAIL_PASSWORD environment variables.'
    
    try:
        recipient = app.config['MAIL_USERNAME']
        if '@' not in recipient:
            app.logger.error('Invalid email format in MAIL_USERNAME')
            return 'Invalid email format in MAIL_USERNAME. Please provide a complete email address.'
            
        msg = Message('Test Email',
                     recipients=[recipient])
        msg.body = 'This is a test email from the authentication system.'
        msg.html = '<h1>Test Email</h1><p>This is a test email from the authentication system.</p>'
        
        app.logger.info(f'Attempting to send test email to {recipient}')
        mail.send(msg)
        
        app.logger.info('Test email sent successfully')
        return 'Test email sent successfully! Check your inbox.'
        
    except Exception as e:
        error_msg = str(e)
        app.logger.error(f'Error sending test email: {error_msg}')
        
        if 'Username and Password not accepted' in error_msg:
            return ('Email authentication failed. Please ensure you are using an App Password '
                   'for Gmail or have enabled Less Secure App Access.')
        
        return f'Error sending test email: {error_msg}'
