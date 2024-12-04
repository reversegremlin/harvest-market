from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from extensions import db
from models import User
from datetime import datetime
import pytz
from pytz import timezone as pytz_timezone
from werkzeug.security import check_password_hash

profile_bp = Blueprint('profile', __name__)
from currency_utils import convert_currency, get_user_balance
from flask import jsonify

@profile_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('profile/dashboard.html', user=current_user, timezone=pytz_timezone)

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        timezone = request.form.get('timezone')
        seasonal_theme = request.form.get('seasonal_theme')
        
        if not all([first_name, last_name, timezone]):
            flash('All fields are required', 'error')
            return redirect(url_for('profile.edit_profile'))
            
        if timezone not in pytz.common_timezones:
            flash('Please select a valid timezone', 'error')
            return redirect(url_for('profile.edit_profile'))
        
        if username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('Username already taken', 'error')
                return redirect(url_for('profile.edit_profile'))
            current_user.username = username
            # Update avatar URL when username changes
            current_user.avatar_url = f"https://api.dicebear.com/6.x/avataaars/svg?seed={username}"
        
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.timezone = timezone
        
        if seasonal_theme in ['autumn', 'winter', 'spring', 'summer']:
            current_user.seasonal_theme = seasonal_theme
        
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('profile.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile', 'error')
            return redirect(url_for('profile.edit_profile'))
    
    return render_template('profile/edit.html', user=current_user, timezones=pytz.common_timezones)

@profile_bp.route('/profile/preview')
def preview_dashboard():
    # Create a mock user with sample data
    mock_user = type('MockUser', (), {
        'username': 'preview_user',
        'email': 'preview@example.com',
        'created_at': datetime.utcnow(),
        'theme': 'autumn',  # Using autumn as the current season
        'avatar_url': '/static/img/default-avatar.svg',
        'seasonal_theme': 'autumn'
    })
    
    return render_template('profile/dashboard.html', user=mock_user, preview_mode=True)

@profile_bp.route('/profile/security', methods=['GET', 'POST'])
@login_required
def security_settings():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate all fields are provided
        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('profile.security_settings'))
        
        # Verify current password
        if not current_user.check_password(current_password):
            current_app.logger.warning(f'Failed password change attempt for user {current_user.username}: incorrect current password')
            flash('Current password is incorrect', 'error')
            return redirect(url_for('profile.security_settings'))
        
        # Validate new password
        validation_errors = []
        if len(new_password) < 8:
            validation_errors.append('Password must be at least 8 characters long')
        if not any(c.isalpha() for c in new_password):
            validation_errors.append('Password must contain at least one letter')
        if not any(c.isdigit() for c in new_password):
            validation_errors.append('Password must contain at least one number')
        if not any(c in '@$!%*#?&' for c in new_password):
            validation_errors.append('Password must contain at least one special character (@$!%*#?&)')
        
        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
            return redirect(url_for('profile.security_settings'))
        
        # Check if passwords match
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('profile.security_settings'))
        
        # Prevent reusing the current password
        if current_user.check_password(new_password):
            flash('New password must be different from your current password', 'error')
            return redirect(url_for('profile.security_settings'))
        
        try:
            # Update password
            current_user.set_password(new_password)
            db.session.commit()
            current_app.logger.info(f'Password successfully changed for user {current_user.username}')
            flash('Password updated successfully', 'success')
            return redirect(url_for('profile.dashboard'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error changing password for user {current_user.username}: {str(e)}')
            flash('An error occurred while updating your password', 'error')
            return redirect(url_for('profile.security_settings'))
    
    # GET request - render the security settings page
    return render_template('profile/security.html')


