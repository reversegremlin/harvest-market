from flask import Blueprint, request, flash, redirect, url_for, render_template, current_app
from flask_login import login_user, logout_user, login_required
from extensions import db
import secrets
import pytz
import requests
from models import User

auth_bp = Blueprint('auth', __name__)

def send_email(to_email, subject, html_content):
    """
    Send email using Mailgun API if configured
    """
    mailgun_api_key = current_app.config.get('MAILGUN_API_KEY')
    mailgun_domain = current_app.config.get('MAILGUN_DOMAIN')
    sender = current_app.config.get('MAIL_DEFAULT_SENDER')

    if not all([mailgun_api_key, mailgun_domain, sender]):
        current_app.logger.warning('Mailgun configuration incomplete, skipping email send')
        return False

    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
            auth=("api", mailgun_api_key),
            data={
                "from": sender,
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
        )
        
        if response.status_code != 200:
            current_app.logger.error(f'Mailgun API error: {response.text}')
            return False
            
        return True
        
    except requests.RequestException as e:
        current_app.logger.error(f'Mailgun API request error: {str(e)}')
        return False

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        timezone = request.form.get('timezone')
        
        # Input validation
        if not all([email, username, password, first_name, last_name, timezone]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.register'))
            
        if not timezone in pytz.common_timezones:
            flash('Please select a valid timezone', 'error')
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
            current_app.logger.warning(f'Registration attempted with existing email: {email}')
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(username=username).first():
            current_app.logger.warning(f'Registration attempted with existing username: {username}')
            flash('Username already taken', 'error')
            return redirect(url_for('auth.register'))

        try:
            # Check if email verification is available
            mailgun_configured = all([
                current_app.config.get('MAILGUN_API_KEY'),
                current_app.config.get('MAILGUN_DOMAIN'),
                current_app.config.get('MAIL_DEFAULT_SENDER')
            ])
            
            if not mailgun_configured:
                current_app.logger.warning('Mailgun not configured, proceeding with registration without email verification')

            # Start database transaction
            user = User(email=email, username=username, first_name=first_name, last_name=last_name, timezone=timezone)
            user.set_password(password)
            user.verification_token = secrets.token_urlsafe(32)
            user.avatar_url = f"https://api.dicebear.com/6.x/avataaars/svg?seed={username}"
            
            db.session.add(user)
            
            if mailgun_configured:
                # Prepare and send verification email
                subject = 'Welcome to Market Harvest - Verify your email'
                html_content = render_template('emails/verify.html', 
                                             token=user.verification_token)
                
                # Attempt to send email
                if send_email(email, subject, html_content):
                    db.session.commit()
                    current_app.logger.info(f'New user registered successfully with email verification: {username} ({email})')
                    flash('Registration successful! Please check your email to verify your account.', 'success')
                else:
                    # Email sending failed but continue with registration
                    user.email_verified = True  # Auto-verify since email sending failed
                    db.session.commit()
                    current_app.logger.warning(f'New user registered without email verification due to email service issues: {username} ({email})')
                    flash('Registration successful! Email verification is currently unavailable.', 'success')
            else:
                # No email verification available
                user.email_verified = True  # Auto-verify since email verification is not available
                db.session.commit()
                current_app.logger.info(f'New user registered without email verification: {username} ({email})')
                flash('Registration successful!', 'success')
            
            return redirect(url_for('auth.login'))
            
        except ValueError as e:
            db.session.rollback()
            current_app.logger.error(f'Configuration error during registration: {str(e)}')
            flash('Email service configuration error. Please contact support.', 'error')
            return redirect(url_for('auth.register'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error during registration for {email}: {str(e)}')
            flash('Unable to send verification email. Please try again later.', 'error')
            return redirect(url_for('auth.register'))
            
    timezones = pytz.common_timezones
    return render_template('auth/register.html', timezones=timezones)

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
            current_app.logger.info(f'User logged in: {user.username}')
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
        current_app.logger.info(f'Email verified for user: {user.username}')
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
            
            try:
                subject = 'Reset your password'
                html_content = render_template('emails/reset_password.html', 
                                            user=user,
                                            token=token)
                if send_email(email, subject, html_content):
                    flash('Password reset instructions sent to your email.', 'success')
                else:
                    flash('Failed to send reset instructions. Please try again later.', 'error')
            except Exception as e:
                current_app.logger.error(f'Error sending reset email: {str(e)}')
                flash('An error occurred. Please try again later.', 'error')
            
            return redirect(url_for('auth.login'))
        else:
            flash('Email address not found.', 'error')
    return render_template('auth/reset_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Both password fields are required.', 'error')
            return render_template('auth/reset_password_confirm.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password_confirm.html')
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/reset_password_confirm.html')
            
        try:
            user.set_password(password)
            user.reset_token = None
            db.session.commit()
            flash('Your password has been reset successfully. You can now login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error resetting password: {str(e)}')
            flash('An error occurred. Please try again later.', 'error')
            
    return render_template('auth/reset_password_confirm.html')

@auth_bp.route('/test-email')
def test_email():
    if not current_app.config['MAILGUN_API_KEY'] or not current_app.config['MAILGUN_DOMAIN']:
        current_app.logger.error('Mailgun configuration missing')
        return 'Mailgun configuration missing. Please check MAILGUN_API_KEY and MAILGUN_DOMAIN environment variables.'
    
    try:
        test_recipient = request.args.get('email', 'test@example.com')
        if '@' not in test_recipient:
            current_app.logger.error('Invalid email format provided')
            return 'Invalid email format. Please provide a valid email address.'
            
        subject = 'Test Email from Market Harvest'
        html_content = '<h1>Test Email</h1><p>This is a test email from the Market Harvest authentication system.</p>'
        
        current_app.logger.info(f'Attempting to send test email to {test_recipient}')
        send_email(test_recipient, subject, html_content)
        
        current_app.logger.info('Test email sent successfully')
        return 'Test email sent successfully! Check your inbox.'
        
    except Exception as e:
        error_msg = str(e)
        current_app.logger.error(f'Error sending test email: {error_msg}')
        return f'Error sending test email: {error_msg}'


@auth_bp.route('/check-username', methods=['POST'])
def check_username():
    username = request.form.get('username')
    
    if not username:
        return {'valid': False, 'message': 'Username is required'}, 400
        
    # Check username format
    if not username.isalnum() and '_' not in username:
        return {'valid': False, 'message': 'Username can only contain letters, numbers, and underscores'}, 400
        
    if len(username) < 3 or len(username) > 20:
        return {'valid': False, 'message': 'Username must be between 3 and 20 characters'}, 400
    
    # Check if username exists
    user = User.query.filter_by(username=username).first()
    if user:
        return {'valid': False, 'message': 'Username already taken'}, 400
        
    return {'valid': True, 'message': 'Username available'}, 200