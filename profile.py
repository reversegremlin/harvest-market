from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from models import User
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('profile/dashboard.html', user=current_user)

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        seasonal_theme = request.form.get('seasonal_theme')
        
        if username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('Username already taken', 'error')
                return redirect(url_for('profile.edit_profile'))
            current_user.username = username
            # Update avatar URL when username changes
            current_user.avatar_url = f"https://api.dicebear.com/6.x/avataaars/svg?seed={username}"
            
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
    
    return render_template('profile/edit.html', user=current_user)

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
