from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from extensions import db, csrf
from models import User, SiteSettings
import logging
from datetime import datetime
import secrets
from auth import send_email

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            current_app.logger.warning(f'Unauthorized admin access attempt by user: {current_user.username}')
            flash('You do not have permission to access this area.', 'error')
            return redirect(url_for('profile.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    users_count = User.query.count()
    unverified_users = User.query.filter_by(email_verified=False).count()
    
    return render_template('admin/dashboard.html',
                         users_count=users_count,
                         unverified_users=unverified_users)

@admin_bp.route('/users')
@admin_required
def user_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )
    
    users = query.paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/user_list.html', users=users, search=search)

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        if user == current_user and not user.is_admin:
            flash('You cannot remove your own admin privileges.', 'error')
            return redirect(url_for('admin.user_list'))
            
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.is_admin = bool(request.form.get('is_admin'))
        user.email_verified = bool(request.form.get('email_verified'))
        
        try:
            db.session.commit()
            current_app.logger.info(f'User {user.username} updated by admin {current_user.username}')
            flash('User updated successfully.', 'success')
            return redirect(url_for('admin.user_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating user {user.username}: {str(e)}')
            flash('Error updating user.', 'error')
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user == current_user:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.user_list'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        current_app.logger.info(f'User {user.username} deleted by admin {current_user.username}')
        flash('User deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting user {user.username}: {str(e)}')
        flash('Error deleting user.', 'error')
    
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/user/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def force_password_reset(user_id):
    user = User.query.get_or_404(user_id)
    
    if user == current_user:
        flash('You cannot force reset your own password.', 'error')
        return redirect(url_for('admin.user_list'))
    
    try:
        user.reset_token = secrets.token_urlsafe(32)
        db.session.commit()
        
        # Send password reset email
        subject = 'Password Reset Required'
        html_content = render_template('emails/admin_reset_password.html', 
                                     user=user,
                                     token=user.reset_token)
        
        if not send_email(user.email, subject, html_content):
            flash('Failed to send password reset email.', 'error')
            return redirect(url_for('admin.user_list'))
            
        current_app.logger.info(f'Password reset forced for user {user.username} by admin {current_user.username}')
        flash('Password reset email sent to user.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error forcing password reset for user {user.username}: {str(e)}')
        flash('Error processing password reset.', 'error')
    
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def site_settings():
    settings = SiteSettings.get_settings()
    
    if request.method == 'POST':
        try:
            settings.site_title = request.form.get('site_title', 'Market Harvest')
            settings.site_icon = request.form.get('site_icon')
            settings.default_theme = request.form.get('default_theme', 'autumn')
            settings.custom_css = request.form.get('custom_css')
            settings.welcome_message = request.form.get('welcome_message')
            settings.footer_text = request.form.get('footer_text')
            settings.updated_at = datetime.utcnow()
            
            current_app.logger.info(f'Updating site settings - default theme: {settings.default_theme}')
            db.session.commit()
            current_app.logger.info(f'Site settings updated by admin {current_user.username}')
            flash('Site settings updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating site settings: {str(e)}')
            flash('Error updating site settings.', 'error')
            
    return render_template('admin/site_settings.html', settings=settings)