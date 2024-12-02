from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from models import User

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
        theme = request.form.get('theme')
        
        if username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('Username already taken', 'error')
                return redirect(url_for('profile.edit_profile'))
            current_user.username = username
            
        current_user.theme = theme
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile.dashboard'))
    
    return render_template('profile/edit.html', user=current_user)
